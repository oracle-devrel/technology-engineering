// Comprehensive UK Postal Code Data
// Full coverage of UK postcode areas with coordinates

export interface PostcodeArea {
  code: string;
  name: string;
  region: string;
  lat: number;
  lng: number;
  population?: number;
}

// All UK Postcode Areas with coordinates
export const ukPostcodeAreas: PostcodeArea[] = [
  // LONDON - Central
  { code: 'EC', name: 'City of London', region: 'London', lat: 51.5155, lng: -0.0922 },
  { code: 'WC', name: 'West Central London', region: 'London', lat: 51.5165, lng: -0.1200 },

  // LONDON - Compass Areas
  { code: 'E', name: 'East London', region: 'London', lat: 51.5450, lng: 0.0553 },
  { code: 'N', name: 'North London', region: 'London', lat: 51.5758, lng: -0.0990 },
  { code: 'NW', name: 'North West London', region: 'London', lat: 51.5520, lng: -0.2100 },
  { code: 'SE', name: 'South East London', region: 'London', lat: 51.4590, lng: -0.0130 },
  { code: 'SW', name: 'South West London', region: 'London', lat: 51.4613, lng: -0.1650 },
  { code: 'W', name: 'West London', region: 'London', lat: 51.5130, lng: -0.2200 },

  // LONDON - Outer
  { code: 'BR', name: 'Bromley', region: 'London', lat: 51.4039, lng: 0.0198 },
  { code: 'CR', name: 'Croydon', region: 'London', lat: 51.3762, lng: -0.0982 },
  { code: 'DA', name: 'Dartford', region: 'London', lat: 51.4462, lng: 0.2190 },
  { code: 'EN', name: 'Enfield', region: 'London', lat: 51.6538, lng: -0.0799 },
  { code: 'HA', name: 'Harrow', region: 'London', lat: 51.5788, lng: -0.3418 },
  { code: 'IG', name: 'Ilford', region: 'London', lat: 51.5590, lng: 0.0741 },
  { code: 'KT', name: 'Kingston upon Thames', region: 'London', lat: 51.4123, lng: -0.3007 },
  { code: 'RM', name: 'Romford', region: 'London', lat: 51.5768, lng: 0.1801 },
  { code: 'SM', name: 'Sutton', region: 'London', lat: 51.3618, lng: -0.1945 },
  { code: 'TW', name: 'Twickenham', region: 'London', lat: 51.4499, lng: -0.3348 },
  { code: 'UB', name: 'Southall', region: 'London', lat: 51.5109, lng: -0.3838 },
  { code: 'WD', name: 'Watford', region: 'London', lat: 51.6565, lng: -0.3903 },

  // SOUTH EAST
  { code: 'AL', name: 'St Albans', region: 'South East', lat: 51.7520, lng: -0.3366 },
  { code: 'BN', name: 'Brighton', region: 'South East', lat: 50.8225, lng: -0.1372 },
  { code: 'CT', name: 'Canterbury', region: 'South East', lat: 51.2802, lng: 1.0789 },
  { code: 'GU', name: 'Guildford', region: 'South East', lat: 51.2362, lng: -0.5704 },
  { code: 'HP', name: 'Hemel Hempstead', region: 'South East', lat: 51.7530, lng: -0.4689 },
  { code: 'LU', name: 'Luton', region: 'South East', lat: 51.8787, lng: -0.4200 },
  { code: 'ME', name: 'Medway', region: 'South East', lat: 51.3884, lng: 0.5472 },
  { code: 'MK', name: 'Milton Keynes', region: 'South East', lat: 52.0406, lng: -0.7594 },
  { code: 'OX', name: 'Oxford', region: 'South East', lat: 51.7520, lng: -1.2577 },
  { code: 'PO', name: 'Portsmouth', region: 'South East', lat: 50.8198, lng: -1.0880 },
  { code: 'RG', name: 'Reading', region: 'South East', lat: 51.4543, lng: -0.9781 },
  { code: 'RH', name: 'Redhill', region: 'South East', lat: 51.2393, lng: -0.1654 },
  { code: 'SG', name: 'Stevenage', region: 'South East', lat: 51.9032, lng: -0.1965 },
  { code: 'SL', name: 'Slough', region: 'South East', lat: 51.5084, lng: -0.5881 },
  { code: 'SN', name: 'Swindon', region: 'South East', lat: 51.5558, lng: -1.7797 },
  { code: 'SO', name: 'Southampton', region: 'South East', lat: 50.9097, lng: -1.4044 },
  { code: 'SS', name: 'Southend-on-Sea', region: 'South East', lat: 51.5459, lng: 0.7077 },
  { code: 'TN', name: 'Tunbridge Wells', region: 'South East', lat: 51.1322, lng: 0.2631 },

  // SOUTH WEST
  { code: 'BA', name: 'Bath', region: 'South West', lat: 51.3758, lng: -2.3599 },
  { code: 'BH', name: 'Bournemouth', region: 'South West', lat: 50.7192, lng: -1.8808 },
  { code: 'BS', name: 'Bristol', region: 'South West', lat: 51.4545, lng: -2.5879 },
  { code: 'DT', name: 'Dorchester', region: 'South West', lat: 50.7151, lng: -2.4366 },
  { code: 'EX', name: 'Exeter', region: 'South West', lat: 50.7184, lng: -3.5339 },
  { code: 'GL', name: 'Gloucester', region: 'South West', lat: 51.8642, lng: -2.2382 },
  { code: 'PL', name: 'Plymouth', region: 'South West', lat: 50.3755, lng: -4.1427 },
  { code: 'SP', name: 'Salisbury', region: 'South West', lat: 51.0688, lng: -1.7945 },
  { code: 'TA', name: 'Taunton', region: 'South West', lat: 51.0147, lng: -3.1029 },
  { code: 'TQ', name: 'Torquay', region: 'South West', lat: 50.4619, lng: -3.5253 },
  { code: 'TR', name: 'Truro', region: 'South West', lat: 50.2632, lng: -5.0510 },

  // EAST OF ENGLAND
  { code: 'CB', name: 'Cambridge', region: 'East', lat: 52.2053, lng: 0.1218 },
  { code: 'CM', name: 'Chelmsford', region: 'East', lat: 51.7356, lng: 0.4685 },
  { code: 'CO', name: 'Colchester', region: 'East', lat: 51.8959, lng: 0.8919 },
  { code: 'IP', name: 'Ipswich', region: 'East', lat: 52.0567, lng: 1.1482 },
  { code: 'NR', name: 'Norwich', region: 'East', lat: 52.6309, lng: 1.2974 },
  { code: 'PE', name: 'Peterborough', region: 'East', lat: 52.5695, lng: -0.2405 },

  // WEST MIDLANDS
  { code: 'B', name: 'Birmingham', region: 'West Midlands', lat: 52.4862, lng: -1.8904 },
  { code: 'CV', name: 'Coventry', region: 'West Midlands', lat: 52.4068, lng: -1.5197 },
  { code: 'DY', name: 'Dudley', region: 'West Midlands', lat: 52.5121, lng: -2.0815 },
  { code: 'HR', name: 'Hereford', region: 'West Midlands', lat: 52.0565, lng: -2.7160 },
  { code: 'ST', name: 'Stoke-on-Trent', region: 'West Midlands', lat: 53.0027, lng: -2.1794 },
  { code: 'TF', name: 'Telford', region: 'West Midlands', lat: 52.6779, lng: -2.4494 },
  { code: 'WR', name: 'Worcester', region: 'West Midlands', lat: 52.1920, lng: -2.2216 },
  { code: 'WS', name: 'Walsall', region: 'West Midlands', lat: 52.5861, lng: -1.9824 },
  { code: 'WV', name: 'Wolverhampton', region: 'West Midlands', lat: 52.5870, lng: -2.1288 },

  // EAST MIDLANDS
  { code: 'DE', name: 'Derby', region: 'East Midlands', lat: 52.9225, lng: -1.4746 },
  { code: 'LE', name: 'Leicester', region: 'East Midlands', lat: 52.6369, lng: -1.1398 },
  { code: 'LN', name: 'Lincoln', region: 'East Midlands', lat: 53.2307, lng: -0.5406 },
  { code: 'NG', name: 'Nottingham', region: 'East Midlands', lat: 52.9548, lng: -1.1581 },
  { code: 'NN', name: 'Northampton', region: 'East Midlands', lat: 52.2405, lng: -0.9027 },

  // YORKSHIRE & HUMBER
  { code: 'BD', name: 'Bradford', region: 'Yorkshire', lat: 53.7960, lng: -1.7594 },
  { code: 'DN', name: 'Doncaster', region: 'Yorkshire', lat: 53.5228, lng: -1.1285 },
  { code: 'HD', name: 'Huddersfield', region: 'Yorkshire', lat: 53.6450, lng: -1.7798 },
  { code: 'HG', name: 'Harrogate', region: 'Yorkshire', lat: 53.9921, lng: -1.5418 },
  { code: 'HU', name: 'Hull', region: 'Yorkshire', lat: 53.7676, lng: -0.3274 },
  { code: 'HX', name: 'Halifax', region: 'Yorkshire', lat: 53.7210, lng: -1.8563 },
  { code: 'LS', name: 'Leeds', region: 'Yorkshire', lat: 53.8008, lng: -1.5491 },
  { code: 'S', name: 'Sheffield', region: 'Yorkshire', lat: 53.3811, lng: -1.4701 },
  { code: 'WF', name: 'Wakefield', region: 'Yorkshire', lat: 53.6833, lng: -1.4977 },
  { code: 'YO', name: 'York', region: 'Yorkshire', lat: 53.9600, lng: -1.0873 },

  // NORTH WEST
  { code: 'BB', name: 'Blackburn', region: 'North West', lat: 53.7500, lng: -2.4833 },
  { code: 'BL', name: 'Bolton', region: 'North West', lat: 53.5780, lng: -2.4299 },
  { code: 'CA', name: 'Carlisle', region: 'North West', lat: 54.8951, lng: -2.9382 },
  { code: 'CH', name: 'Chester', region: 'North West', lat: 53.1905, lng: -2.8909 },
  { code: 'CW', name: 'Crewe', region: 'North West', lat: 53.0985, lng: -2.4404 },
  { code: 'FY', name: 'Blackpool', region: 'North West', lat: 53.8142, lng: -3.0503 },
  { code: 'L', name: 'Liverpool', region: 'North West', lat: 53.4084, lng: -2.9916 },
  { code: 'LA', name: 'Lancaster', region: 'North West', lat: 54.0465, lng: -2.8007 },
  { code: 'M', name: 'Manchester', region: 'North West', lat: 53.4808, lng: -2.2426 },
  { code: 'OL', name: 'Oldham', region: 'North West', lat: 53.5409, lng: -2.1114 },
  { code: 'PR', name: 'Preston', region: 'North West', lat: 53.7632, lng: -2.7031 },
  { code: 'SK', name: 'Stockport', region: 'North West', lat: 53.4083, lng: -2.1494 },
  { code: 'WA', name: 'Warrington', region: 'North West', lat: 53.3900, lng: -2.5970 },
  { code: 'WN', name: 'Wigan', region: 'North West', lat: 53.5448, lng: -2.6318 },

  // NORTH EAST
  { code: 'DH', name: 'Durham', region: 'North East', lat: 54.7761, lng: -1.5733 },
  { code: 'DL', name: 'Darlington', region: 'North East', lat: 54.5234, lng: -1.5526 },
  { code: 'NE', name: 'Newcastle upon Tyne', region: 'North East', lat: 54.9783, lng: -1.6178 },
  { code: 'SR', name: 'Sunderland', region: 'North East', lat: 54.9069, lng: -1.3838 },
  { code: 'TS', name: 'Cleveland', region: 'North East', lat: 54.5681, lng: -1.2341 },

  // SCOTLAND
  { code: 'AB', name: 'Aberdeen', region: 'Scotland', lat: 57.1497, lng: -2.0943 },
  { code: 'DD', name: 'Dundee', region: 'Scotland', lat: 56.4620, lng: -2.9707 },
  { code: 'DG', name: 'Dumfries', region: 'Scotland', lat: 55.0700, lng: -3.6100 },
  { code: 'EH', name: 'Edinburgh', region: 'Scotland', lat: 55.9533, lng: -3.1883 },
  { code: 'FK', name: 'Falkirk', region: 'Scotland', lat: 56.0019, lng: -3.7839 },
  { code: 'G', name: 'Glasgow', region: 'Scotland', lat: 55.8642, lng: -4.2518 },
  { code: 'HS', name: 'Outer Hebrides', region: 'Scotland', lat: 57.7600, lng: -7.0200 },
  { code: 'IV', name: 'Inverness', region: 'Scotland', lat: 57.4778, lng: -4.2247 },
  { code: 'KA', name: 'Kilmarnock', region: 'Scotland', lat: 55.6111, lng: -4.4958 },
  { code: 'KW', name: 'Kirkwall (Orkney)', region: 'Scotland', lat: 58.9845, lng: -2.9596 },
  { code: 'KY', name: 'Kirkcaldy', region: 'Scotland', lat: 56.1132, lng: -3.1596 },
  { code: 'ML', name: 'Motherwell', region: 'Scotland', lat: 55.7893, lng: -3.9916 },
  { code: 'PA', name: 'Paisley', region: 'Scotland', lat: 55.8466, lng: -4.4237 },
  { code: 'PH', name: 'Perth', region: 'Scotland', lat: 56.3950, lng: -3.4308 },
  { code: 'TD', name: 'Galashiels', region: 'Scotland', lat: 55.6186, lng: -2.8046 },
  { code: 'ZE', name: 'Shetland', region: 'Scotland', lat: 60.3880, lng: -1.0660 },

  // WALES
  { code: 'CF', name: 'Cardiff', region: 'Wales', lat: 51.4816, lng: -3.1791 },
  { code: 'LD', name: 'Llandrindod Wells', region: 'Wales', lat: 52.2425, lng: -3.3818 },
  { code: 'LL', name: 'Llandudno', region: 'Wales', lat: 53.3241, lng: -3.8276 },
  { code: 'NP', name: 'Newport', region: 'Wales', lat: 51.5842, lng: -2.9977 },
  { code: 'SA', name: 'Swansea', region: 'Wales', lat: 51.6214, lng: -3.9436 },
  { code: 'SY', name: 'Shrewsbury', region: 'Wales', lat: 52.7073, lng: -2.7538 },

  // NORTHERN IRELAND
  { code: 'BT', name: 'Belfast', region: 'Northern Ireland', lat: 54.5973, lng: -5.9301 },

  // CROWN DEPENDENCIES
  { code: 'GY', name: 'Guernsey', region: 'Channel Islands', lat: 49.4530, lng: -2.5350 },
  { code: 'JE', name: 'Jersey', region: 'Channel Islands', lat: 49.2144, lng: -2.1312 },
  { code: 'IM', name: 'Isle of Man', region: 'Isle of Man', lat: 54.2361, lng: -4.5481 },
];

// Generate a realistic UK postcode
export function generateUKPostcode(areaCode: string): string {
  const district = Math.floor(Math.random() * 20) + 1;
  const sector = Math.floor(Math.random() * 9) + 1;
  const unit = String.fromCharCode(65 + Math.floor(Math.random() * 26)) +
               String.fromCharCode(65 + Math.floor(Math.random() * 26));
  return `${areaCode}${district} ${sector}${unit}`;
}

// Get postcode area by coordinates (nearest)
export function getNearestPostcodeArea(lat: number, lng: number): PostcodeArea {
  let nearest = ukPostcodeAreas[0];
  let minDist = Infinity;

  for (const area of ukPostcodeAreas) {
    const dist = Math.sqrt(
      Math.pow(area.lat - lat, 2) + Math.pow(area.lng - lng, 2)
    );
    if (dist < minDist) {
      minDist = dist;
      nearest = area;
    }
  }

  return nearest;
}

// Get all postcode areas for a region
export function getPostcodesByRegion(region: string): PostcodeArea[] {
  return ukPostcodeAreas.filter(area => area.region === region);
}

// Get regions list
export function getUKRegions(): string[] {
  return [...new Set(ukPostcodeAreas.map(area => area.region))];
}

// UK Major Cities for benchmarks
export const ukMajorCities = [
  { name: 'London', lat: 51.5074, lng: -0.1278, population: 8982000 },
  { name: 'Birmingham', lat: 52.4862, lng: -1.8904, population: 1141816 },
  { name: 'Manchester', lat: 53.4808, lng: -2.2426, population: 553230 },
  { name: 'Leeds', lat: 53.8008, lng: -1.5491, population: 789194 },
  { name: 'Glasgow', lat: 55.8642, lng: -4.2518, population: 633120 },
  { name: 'Liverpool', lat: 53.4084, lng: -2.9916, population: 498042 },
  { name: 'Bristol', lat: 51.4545, lng: -2.5879, population: 463405 },
  { name: 'Sheffield', lat: 53.3811, lng: -1.4701, population: 584853 },
  { name: 'Edinburgh', lat: 55.9533, lng: -3.1883, population: 524930 },
  { name: 'Leicester', lat: 52.6369, lng: -1.1398, population: 354224 },
  { name: 'Coventry', lat: 52.4068, lng: -1.5197, population: 371521 },
  { name: 'Bradford', lat: 53.7960, lng: -1.7594, population: 537173 },
  { name: 'Cardiff', lat: 51.4816, lng: -3.1791, population: 362756 },
  { name: 'Belfast', lat: 54.5973, lng: -5.9301, population: 343542 },
  { name: 'Nottingham', lat: 52.9548, lng: -1.1581, population: 331069 },
  { name: 'Newcastle', lat: 54.9783, lng: -1.6178, population: 302820 },
  { name: 'Southampton', lat: 50.9097, lng: -1.4044, population: 252796 },
  { name: 'Portsmouth', lat: 50.8198, lng: -1.0880, population: 238800 },
  { name: 'Brighton', lat: 50.8225, lng: -0.1372, population: 229700 },
  { name: 'Plymouth', lat: 50.3755, lng: -4.1427, population: 262100 },
  { name: 'Reading', lat: 51.4543, lng: -0.9781, population: 218705 },
  { name: 'Derby', lat: 52.9225, lng: -1.4746, population: 257302 },
  { name: 'Wolverhampton', lat: 52.5870, lng: -2.1288, population: 262008 },
  { name: 'Aberdeen', lat: 57.1497, lng: -2.0943, population: 228990 },
  { name: 'Swansea', lat: 51.6214, lng: -3.9436, population: 246563 },
];

// Generate stops using realistic UK postcodes
export function generateUKStops(
  count: number,
  options: {
    region?: string;
    centerLat?: number;
    centerLng?: number;
    radiusKm?: number;
  } = {}
): Array<{
  id: number;
  lat: number;
  lng: number;
  demand: number;
  label: string;
  postcode: string;
  region: string;
}> {
  const { region, centerLat = 54.5, centerLng = -2.0, radiusKm = 400 } = options;
  const stops = [];

  // Filter areas by region if specified
  let availableAreas = region
    ? ukPostcodeAreas.filter(a => a.region === region)
    : ukPostcodeAreas;

  // Filter by radius if center is specified
  if (centerLat && centerLng && radiusKm) {
    const radiusDeg = radiusKm / 111;
    availableAreas = availableAreas.filter(area => {
      const dist = Math.sqrt(
        Math.pow(area.lat - centerLat, 2) +
        Math.pow(area.lng - centerLng, 2)
      );
      return dist <= radiusDeg;
    });
  }

  // Fallback to all areas if none match
  if (availableAreas.length === 0) {
    availableAreas = ukPostcodeAreas;
  }

  for (let i = 0; i < count; i++) {
    // Pick a random area
    const area = availableAreas[Math.floor(Math.random() * availableAreas.length)];

    // Add variation around the area center (up to ~5km)
    const variation = 0.05;
    const lat = area.lat + (Math.random() - 0.5) * variation * 2;
    const lng = area.lng + (Math.random() - 0.5) * variation * 2;

    stops.push({
      id: i + 1,
      lat,
      lng,
      demand: Math.floor(Math.random() * 10) + 1,
      label: `${area.name} Stop ${i + 1}`,
      postcode: generateUKPostcode(area.code),
      region: area.region,
    });
  }

  return stops;
}

// Belron-specific data (Autoglass/Carglass)
export const belronJobTypes = {
  CHIP_REPAIR: {
    name: 'Chip Repair',
    minDuration: 30,
    maxDuration: 60,
    avgDuration: 45,
    requiresRecalibration: false,
    revenue: 85,
    margin: 0.65,
  },
  REPLACEMENT: {
    name: 'Windscreen Replacement',
    minDuration: 90,
    maxDuration: 120,
    avgDuration: 90,
    requiresRecalibration: true,
    recalibrationRate: 0.60, // 60% of replacements need recalibration
    revenue: 350,
    margin: 0.40,
  },
  RECALIBRATION: {
    name: 'ADAS Recalibration',
    minDuration: 60,
    maxDuration: 90,
    avgDuration: 75,
    requiresRecalibration: false,
    revenue: 180,
    margin: 0.55,
  },
};

// Generate Belron-specific stops
export function generateBelronStops(
  count: number,
  region: string = 'London'
): Array<{
  id: number;
  lat: number;
  lng: number;
  demand: number;
  label: string;
  postcode: string;
  jobType: keyof typeof belronJobTypes;
  serviceDuration: number;
  requiresRecalibration: boolean;
  revenue: number;
  priority: number;
}> {
  const stops = [];
  const areas = getPostcodesByRegion(region);

  if (areas.length === 0) {
    throw new Error(`No postcode areas found for region: ${region}`);
  }

  for (let i = 0; i < count; i++) {
    const area = areas[Math.floor(Math.random() * areas.length)];

    // 75% replacements, 25% repairs (as per Belron feedback)
    const isReplacement = Math.random() < 0.75;
    const jobType = isReplacement ? 'REPLACEMENT' : 'CHIP_REPAIR';
    const job = belronJobTypes[jobType];

    // Calculate service duration
    let serviceDuration = job.avgDuration;
    let requiresRecalibration = false;

    if (isReplacement && Math.random() < belronJobTypes.REPLACEMENT.recalibrationRate) {
      requiresRecalibration = true;
      serviceDuration += belronJobTypes.RECALIBRATION.avgDuration;
    }

    // Add variation
    const lat = area.lat + (Math.random() - 0.5) * 0.1;
    const lng = area.lng + (Math.random() - 0.5) * 0.1;

    stops.push({
      id: i + 1,
      lat,
      lng,
      demand: 1,
      label: `${job.name} - ${area.name}`,
      postcode: generateUKPostcode(area.code),
      jobType: jobType as keyof typeof belronJobTypes,
      serviceDuration,
      requiresRecalibration,
      revenue: job.revenue + (requiresRecalibration ? belronJobTypes.RECALIBRATION.revenue : 0),
      priority: isReplacement ? 2 : 1, // Replacements are higher priority
    });
  }

  return stops;
}
