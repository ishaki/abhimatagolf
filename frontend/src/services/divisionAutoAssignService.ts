import { Participant } from './participantService';
import { EventDivision } from './eventDivisionService';
import api from './api';

export interface AutoAssignResult {
  total: number;
  assigned: number;
  skipped: number;
  errors: Array<{
    participantName?: string;
    participant_id?: number;
    reason?: string;
    error?: string;
  }>;
}

interface DivisionAssignment {
  participant_id: number;
  division_id: number | null;
  division_name: string | null;
}

/**
 * Auto-assign divisions to participants based on:
 * 1. Sex field (Female → Ladies division)
 * 2. Name keywords (Senior → Senior division)
 * 3. Handicap range matching
 * 
 * Uses bulk API endpoint to avoid rate limits
 */
export async function autoAssignDivisions(
  participants: Participant[],
  divisions: EventDivision[]
): Promise<AutoAssignResult> {
  if (divisions.length === 0) {
    return {
      total: participants.length,
      assigned: 0,
      skipped: participants.length,
      errors: [{
        participantName: 'All',
        reason: 'No divisions available for this event',
      }],
    };
  }

  // Build assignments for participants without divisions
  const assignments: DivisionAssignment[] = [];
  const skippedParticipants: string[] = [];
  const noMatchParticipants: Array<{participantName: string; reason: string}> = [];

  for (const participant of participants) {
    // Skip if already assigned to a division
    if (participant.division_id) {
      skippedParticipants.push(participant.name);
      continue;
    }

    const matchedDivision = findBestDivisionMatch(participant, divisions);

    if (matchedDivision) {
      assignments.push({
        participant_id: participant.id,
        division_id: matchedDivision.id,
        division_name: matchedDivision.name,
      });
    } else {
      noMatchParticipants.push({
        participantName: participant.name,
        reason: 'No matching division found',
      });
    }
  }

  // If no assignments to make, return early
  if (assignments.length === 0) {
    return {
      total: participants.length,
      assigned: 0,
      skipped: participants.length,
      errors: noMatchParticipants,
    };
  }

  // Make single bulk API call
  try {
    const response = await api.post('/participants/bulk-assign-divisions', {
      assignments,
    });

    const backendResult = response.data;

    // Merge backend errors with frontend no-match errors
    const allErrors = [
      ...noMatchParticipants,
      ...backendResult.errors.map((err: any) => ({
        participantName: `Participant #${err.participant_id}`,
        reason: err.error || 'Unknown error',
      })),
    ];

    return {
      total: participants.length,
      assigned: backendResult.assigned,
      skipped: skippedParticipants.length + backendResult.skipped + noMatchParticipants.length,
      errors: allErrors,
    };
  } catch (error: any) {
    console.error('Bulk assignment error:', error);
    throw new Error(
      error.response?.data?.detail || 
      error.message || 
      'Failed to assign divisions'
    );
  }
}

/**
 * Find the best matching division for a participant
 * Priority:
 * 1. Senior division (if name contains "senior" + handicap matches)
 * 2. Ladies division (if sex = Female + handicap matches)
 * 3. Best handicap match
 */
function findBestDivisionMatch(
  participant: Participant,
  divisions: EventDivision[]
): EventDivision | null {
  const handicap = participant.declared_handicap;
  const name = participant.name.toLowerCase();
  const sex = participant.sex?.toLowerCase();

  // Helper function to check if handicap fits division range
  const handicapFits = (division: EventDivision): boolean => {
    const minFits = division.handicap_min === null || handicap >= division.handicap_min;
    const maxFits = division.handicap_max === null || handicap <= division.handicap_max;
    return minFits && maxFits;
  };

  // Helper function to check division capacity
  const hasCapacity = (division: EventDivision): boolean => {
    if (division.max_participants === null) return true;
    return (division.current_participants || 0) < division.max_participants;
  };

  // Filter divisions with capacity
  const availableDivisions = divisions.filter(hasCapacity);

  if (availableDivisions.length === 0) {
    return null;
  }

  // Priority 1: Senior division (name contains "senior" or "sr")
  if (name.includes('senior') || name.includes(' sr ') || name.includes(' sr.')) {
    const seniorDivision = availableDivisions.find(
      (div) =>
        (div.name.toLowerCase().includes('senior') || div.name.toLowerCase().includes('sr')) &&
        handicapFits(div)
    );
    if (seniorDivision) return seniorDivision;
  }

  // Priority 2: Ladies division (sex = Female)
  if (sex === 'female') {
    const ladiesDivision = availableDivisions.find(
      (div) =>
        (div.name.toLowerCase().includes('ladies') || 
         div.name.toLowerCase().includes('women') ||
         div.name.toLowerCase().includes('female')) &&
        handicapFits(div)
    );
    if (ladiesDivision) return ladiesDivision;
  }

  // Priority 3: Best handicap match
  const matchingDivisions = availableDivisions.filter(handicapFits);

  if (matchingDivisions.length === 0) {
    return null;
  }

  // If multiple matches, prefer the one with most specific range (smallest range)
  matchingDivisions.sort((a, b) => {
    const rangeA = (a.handicap_max || 54) - (a.handicap_min || 0);
    const rangeB = (b.handicap_max || 54) - (b.handicap_min || 0);
    return rangeA - rangeB;
  });

  return matchingDivisions[0];
}

