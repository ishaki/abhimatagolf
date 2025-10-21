import React, { useState, useMemo } from 'react';
import { Input } from '@/components/ui/input';
import { Search } from 'lucide-react';

interface Participant {
  id: number;
  name: string;
  declared_handicap: number;
  division?: string;
  holes_completed?: number;
  gross_score?: number;
}

interface ParticipantSelectorProps {
  participants: Participant[];
  selectedParticipantId: number | null;
  onSelectParticipant: (participantId: number) => void;
}

const ParticipantSelector: React.FC<ParticipantSelectorProps> = ({
  participants,
  selectedParticipantId,
  onSelectParticipant,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  // Filter participants based on search query
  const filteredParticipants = useMemo(() => {
    if (!searchQuery.trim()) return participants;

    const query = searchQuery.toLowerCase();
    return participants.filter(p =>
      p.name.toLowerCase().includes(query) ||
      p.division?.toLowerCase().includes(query)
    );
  }, [participants, searchQuery]);

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <Input
          type="text"
          placeholder="Search participant by name or division..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Participants Table */}
      <div className="border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Handicap
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Division
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Holes
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Score
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredParticipants.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                    {searchQuery ? 'No participants found matching your search' : 'No participants available'}
                  </td>
                </tr>
              ) : (
                filteredParticipants.map((participant) => (
                  <tr
                    key={participant.id}
                    onClick={() => onSelectParticipant(participant.id)}
                    className={`cursor-pointer transition-colors hover:bg-blue-50 ${
                      selectedParticipantId === participant.id
                        ? 'bg-blue-100 border-l-4 border-blue-500'
                        : ''
                    }`}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{participant.name}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {participant.declared_handicap}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-600">
                      {participant.division || '-'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center text-sm text-gray-600">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {participant.holes_completed || 0}/18
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-center text-sm font-semibold text-gray-900">
                      {participant.gross_score || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary */}
      <div className="text-sm text-gray-500">
        Showing {filteredParticipants.length} of {participants.length} participants
      </div>
    </div>
  );
};

export default ParticipantSelector;
