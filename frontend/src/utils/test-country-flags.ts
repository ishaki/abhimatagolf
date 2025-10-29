/**
 * Test script to verify country flag functionality
 *
 * Run in browser console to test flag emojis:
 * import { testCountryFlags } from './utils/test-country-flags'
 * testCountryFlags()
 */

import { getCountryFlag, getCountryCode } from './countryUtils';

export const testCountryFlags = () => {
  console.log('🧪 Testing Country Flag Functionality');
  console.log('=====================================\n');

  // Test common countries
  const testCountries = [
    'Indonesia',
    'Singapore',
    'Malaysia',
    'Thailand',
    'United States',
    'United Kingdom',
    'Australia',
    'Japan',
    'ID', // Test ISO code
    'SG',
    'MY'
  ];

  console.log('📍 Testing Country Names and Codes:');
  testCountries.forEach(country => {
    const code = getCountryCode(country);
    const flag = getCountryFlag(country);

    console.log(`${country.padEnd(20)} → Code: ${code || 'NOT FOUND'} → Flag: ${flag || '❌ NO FLAG'}`);
  });

  console.log('\n🌐 Your browser flag emoji support:');
  console.log('Indonesia 🇮🇩 Singapore 🇸🇬 Malaysia 🇲🇾 Thailand 🇹🇭');
  console.log('USA 🇺🇸 UK 🇬🇧 Japan 🇯🇵 Australia 🇦🇺');

  console.log('\n💡 Troubleshooting:');
  console.log('If you see � or boxes instead of flags, your system/browser may not support flag emojis.');
  console.log('Flags should now show with country names in the Participant List regardless.');
};

// Auto-run in development
if (import.meta.env.DEV) {
  console.log('💡 Country flag test available. Run: testCountryFlags()');
}
