// Country name to ISO 3166-1 alpha-2 code mapping
export const countryCodeMap: Record<string, string> = {
  'United States': 'US',
  'United Kingdom': 'GB',
  'Canada': 'CA',
  'Australia': 'AU',
  'Germany': 'DE',
  'France': 'FR',
  'Japan': 'JP',
  'South Korea': 'KR',
  'China': 'CN',
  'India': 'IN',
  'Brazil': 'BR',
  'Mexico': 'MX',
  'Spain': 'ES',
  'Italy': 'IT',
  'Netherlands': 'NL',
  'Sweden': 'SE',
  'Norway': 'NO',
  'Denmark': 'DK',
  'Finland': 'FI',
  'Switzerland': 'CH',
  'Austria': 'AT',
  'Belgium': 'BE',
  'Ireland': 'IE',
  'Portugal': 'PT',
  'Poland': 'PL',
  'Czech Republic': 'CZ',
  'Hungary': 'HU',
  'Romania': 'RO',
  'Bulgaria': 'BG',
  'Croatia': 'HR',
  'Slovenia': 'SI',
  'Slovakia': 'SK',
  'Estonia': 'EE',
  'Latvia': 'LV',
  'Lithuania': 'LT',
  'Greece': 'GR',
  'Cyprus': 'CY',
  'Malta': 'MT',
  'Luxembourg': 'LU',
  'Iceland': 'IS',
  'Liechtenstein': 'LI',
  'Monaco': 'MC',
  'San Marino': 'SM',
  'Vatican City': 'VA',
  'Andorra': 'AD',
  'Malaysia': 'MY',
  'Singapore': 'SG',
  'Thailand': 'TH',
  'Indonesia': 'ID',
  'Philippines': 'PH',
  'Vietnam': 'VN',
  'Taiwan': 'TW',
  'Hong Kong': 'HK',
  'Macau': 'MO',
  'New Zealand': 'NZ',
  'South Africa': 'ZA',
  'Egypt': 'EG',
  'Nigeria': 'NG',
  'Kenya': 'KE',
  'Morocco': 'MA',
  'Tunisia': 'TN',
  'Algeria': 'DZ',
  'Libya': 'LY',
  'Sudan': 'SD',
  'Ethiopia': 'ET',
  'Ghana': 'GH',
  'Senegal': 'SN',
  'Ivory Coast': 'CI',
  'Cameroon': 'CM',
  'Uganda': 'UG',
  'Tanzania': 'TZ',
  'Madagascar': 'MG',
  'Mozambique': 'MZ',
  'Angola': 'AO',
  'Zambia': 'ZM',
  'Zimbabwe': 'ZW',
  'Botswana': 'BW',
  'Namibia': 'NA',
  'Lesotho': 'LS',
  'Swaziland': 'SZ',
  'Mauritius': 'MU',
  'Seychelles': 'SC',
  'Argentina': 'AR',
  'Chile': 'CL',
  'Peru': 'PE',
  'Colombia': 'CO',
  'Venezuela': 'VE',
  'Ecuador': 'EC',
  'Bolivia': 'BO',
  'Paraguay': 'PY',
  'Uruguay': 'UY',
  'Guyana': 'GY',
  'Suriname': 'SR',
  'French Guiana': 'GF',
  'Russia': 'RU',
  'Ukraine': 'UA',
  'Belarus': 'BY',
  'Moldova': 'MD',
  'Georgia': 'GE',
  'Armenia': 'AM',
  'Azerbaijan': 'AZ',
  'Kazakhstan': 'KZ',
  'Uzbekistan': 'UZ',
  'Kyrgyzstan': 'KG',
  'Tajikistan': 'TJ',
  'Turkmenistan': 'TM',
  'Afghanistan': 'AF',
  'Pakistan': 'PK',
  'Bangladesh': 'BD',
  'Sri Lanka': 'LK',
  'Maldives': 'MV',
  'Nepal': 'NP',
  'Bhutan': 'BT',
  'Myanmar': 'MM',
  'Laos': 'LA',
  'Cambodia': 'KH',
  'Mongolia': 'MN',
  'North Korea': 'KP',
  'Israel': 'IL',
  'Palestine': 'PS',
  'Jordan': 'JO',
  'Lebanon': 'LB',
  'Syria': 'SY',
  'Iraq': 'IQ',
  'Iran': 'IR',
  'Turkey': 'TR',
  'Saudi Arabia': 'SA',
  'United Arab Emirates': 'AE',
  'Qatar': 'QA',
  'Kuwait': 'KW',
  'Bahrain': 'BH',
  'Oman': 'OM',
  'Yemen': 'YE'
};

// Function to convert country code to flag emoji
const getFlagEmoji = (countryCode: string): string => {
  const codePoints = countryCode
    .toUpperCase()
    .split('')
    .map(char => 127397 + char.charCodeAt(0));
  return String.fromCodePoint(...codePoints);
};

export const getCountryCode = (countryName: string): string | null => {
  if (!countryName) return null;
  
  // Direct lookup
  const directMatch = countryCodeMap[countryName];
  if (directMatch) return directMatch;
  
  // Case-insensitive lookup
  const lowerCountryName = countryName.toLowerCase();
  for (const [name, code] of Object.entries(countryCodeMap)) {
    if (name.toLowerCase() === lowerCountryName) {
      return code;
    }
  }
  
  return null;
};

export const getCountryFlag = (countryName: string): string | null => {
  const countryCode = getCountryCode(countryName);
  return countryCode ? getFlagEmoji(countryCode) : null;
};
