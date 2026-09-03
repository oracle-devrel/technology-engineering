// Formatting utilities

export function formatDistance(km: number): string {
  if (km >= 1000) {
    return `${(km / 1000).toFixed(1)}K km`;
  }
  return `${km.toFixed(1)} km`;
}

export function formatDuration(minutes: number): string {
  if (minutes >= 60) {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  }
  return `${Math.round(minutes)} min`;
}

export function formatSolveTime(ms: number): string {
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(2)}s`;
  }
  return `${Math.round(ms)}ms`;
}

export function formatBytes(bytes: number): string {
  if (bytes >= 1024 * 1024 * 1024) {
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
  }
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(2)} KB`;
  }
  return `${bytes} B`;
}

export function formatNumber(num: number): string {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toLocaleString();
}

export function formatPercent(value: number, total: number): string {
  if (total === 0) return '0%';
  return `${((value / total) * 100).toFixed(1)}%`;
}

export function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDate(date: Date): string {
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

// Country-specific Vehicle Registration Plates
// Each country has its own format and regional names

interface VehiclePlateInfo {
  plate: string;
  region: string;
  name: string;
}

const VEHICLE_PLATES_BY_COUNTRY: Record<string, VehiclePlateInfo[]> = {
  // UK - Format: AA00 AAA
  GB: [
    { plate: 'LN24 FLT', region: 'London', name: 'Fleet Van 1' },
    { plate: 'LM24 DEL', region: 'London', name: 'Delivery Van 2' },
    { plate: 'LC73 EXP', region: 'London', name: 'Express 1' },
    { plate: 'LE73 FLD', region: 'London', name: 'Field Van 1' },
    { plate: 'BD51 SMR', region: 'Birmingham', name: 'Midlands 1' },
    { plate: 'BG67 RTE', region: 'Birmingham', name: 'Route Van 1' },
    { plate: 'BK22 SVC', region: 'Birmingham', name: 'Service Van 1' },
    { plate: 'MA19 NTH', region: 'Manchester', name: 'North Van 1' },
    { plate: 'MC24 PRO', region: 'Manchester', name: 'Pro Van 1' },
    { plate: 'MK71 FLT', region: 'Manchester', name: 'Fleet 1' },
    { plate: 'YA23 YRK', region: 'Leeds', name: 'Yorkshire 1' },
    { plate: 'YC65 DLV', region: 'Leeds', name: 'Delivery 1' },
    { plate: 'SA21 SCT', region: 'Edinburgh', name: 'Scotland 1' },
    { plate: 'SC74 HGH', region: 'Edinburgh', name: 'Highland Van' },
    { plate: 'SG18 EDN', region: 'Edinburgh', name: 'Edinburgh Van' },
    { plate: 'CA20 WLS', region: 'Cardiff', name: 'Wales Van 1' },
    { plate: 'CY69 CYM', region: 'Cardiff', name: 'Cymru Van' },
    { plate: 'WA22 SWT', region: 'Bristol', name: 'Southwest 1' },
    { plate: 'WC17 BST', region: 'Bristol', name: 'Bristol Van' },
    { plate: 'NA23 NES', region: 'Newcastle', name: 'Northeast 1' },
    { plate: 'NC66 TYN', region: 'Newcastle', name: 'Tyne Van' },
    { plate: 'EV24 CHG', region: 'Electric', name: 'EV Charger Van' },
    { plate: 'NT24 NET', region: 'National', name: 'Network Van' },
    { plate: 'FL73 MGR', region: 'Fleet', name: 'Fleet Manager' },
    { plate: 'RP24 SPD', region: 'Rapid', name: 'Rapid Response' },
    { plate: 'SV19 TEC', region: 'Service', name: 'Tech Service' },
    { plate: 'MT24 VAN', region: 'Maintenance', name: 'Maint Van 1' },
    { plate: 'DL21 EXP', region: 'Delivery', name: 'Express Del' },
    { plate: 'FE74 SRV', region: 'Field', name: 'Field Service' },
    { plate: 'UK24 NAT', region: 'National', name: 'National Van' },
  ],
  // France - Format: AA-123-BB
  FR: [
    { plate: 'AB-123-CD', region: 'Paris', name: 'Véhicule 1' },
    { plate: 'CD-234-EF', region: 'Paris', name: 'Véhicule 2' },
    { plate: 'EF-345-GH', region: 'Lyon', name: 'Lyon Van 1' },
    { plate: 'GH-456-IJ', region: 'Lyon', name: 'Lyon Van 2' },
    { plate: 'IJ-567-KL', region: 'Marseille', name: 'Marseille 1' },
    { plate: 'KL-678-MN', region: 'Marseille', name: 'Marseille 2' },
    { plate: 'MN-789-OP', region: 'Toulouse', name: 'Toulouse 1' },
    { plate: 'OP-890-QR', region: 'Bordeaux', name: 'Bordeaux 1' },
    { plate: 'QR-901-ST', region: 'Lille', name: 'Lille Van 1' },
    { plate: 'ST-012-UV', region: 'Nice', name: 'Nice Van 1' },
    { plate: 'UV-123-WX', region: 'Nantes', name: 'Nantes 1' },
    { plate: 'WX-234-YZ', region: 'Strasbourg', name: 'Strasbourg 1' },
    { plate: 'YZ-345-AB', region: 'Rennes', name: 'Rennes Van 1' },
    { plate: 'BC-456-DE', region: 'Reims', name: 'Reims Van 1' },
    { plate: 'DE-567-FG', region: 'Montpellier', name: 'Montpellier 1' },
    { plate: 'FG-678-HI', region: 'Paris', name: 'Paris Fleet 1' },
    { plate: 'HI-789-JK', region: 'Paris', name: 'Paris Fleet 2' },
    { plate: 'JK-890-LM', region: 'Paris', name: 'Paris Express' },
    { plate: 'LM-901-NO', region: 'Paris', name: 'Paris Service' },
    { plate: 'NO-012-PQ', region: 'Paris', name: 'Paris Rapid' },
  ],
  // Germany - Format: B AB 1234
  DE: [
    { plate: 'B AB 1234', region: 'Berlin', name: 'Berlin Van 1' },
    { plate: 'B CD 2345', region: 'Berlin', name: 'Berlin Van 2' },
    { plate: 'M EF 3456', region: 'Munich', name: 'München 1' },
    { plate: 'M GH 4567', region: 'Munich', name: 'München 2' },
    { plate: 'F IJ 5678', region: 'Frankfurt', name: 'Frankfurt 1' },
    { plate: 'HH KL 6789', region: 'Hamburg', name: 'Hamburg 1' },
    { plate: 'K MN 7890', region: 'Cologne', name: 'Köln Van 1' },
    { plate: 'D OP 8901', region: 'Düsseldorf', name: 'Düsseldorf 1' },
    { plate: 'S QR 9012', region: 'Stuttgart', name: 'Stuttgart 1' },
    { plate: 'L ST 0123', region: 'Leipzig', name: 'Leipzig Van 1' },
    { plate: 'N UV 1234', region: 'Nuremberg', name: 'Nürnberg 1' },
    { plate: 'DO WX 2345', region: 'Dortmund', name: 'Dortmund 1' },
    { plate: 'E YZ 3456', region: 'Essen', name: 'Essen Van 1' },
    { plate: 'HB AB 4567', region: 'Bremen', name: 'Bremen Van 1' },
    { plate: 'DD CD 5678', region: 'Dresden', name: 'Dresden Van 1' },
  ],
  // USA - Format: ABC1234
  US: [
    { plate: 'ABC1234', region: 'New York', name: 'NY Fleet 1' },
    { plate: 'DEF2345', region: 'New York', name: 'NY Fleet 2' },
    { plate: 'GHI3456', region: 'Los Angeles', name: 'LA Van 1' },
    { plate: 'JKL4567', region: 'Los Angeles', name: 'LA Van 2' },
    { plate: 'MNO5678', region: 'Chicago', name: 'Chicago 1' },
    { plate: 'PQR6789', region: 'Houston', name: 'Houston 1' },
    { plate: 'STU7890', region: 'Phoenix', name: 'Phoenix 1' },
    { plate: 'VWX8901', region: 'Philadelphia', name: 'Philly Van 1' },
    { plate: 'YZA9012', region: 'San Antonio', name: 'San Antonio 1' },
    { plate: 'BCD0123', region: 'San Diego', name: 'San Diego 1' },
    { plate: 'EFG1234', region: 'Dallas', name: 'Dallas Van 1' },
    { plate: 'HIJ2345', region: 'San Jose', name: 'San Jose 1' },
    { plate: 'KLM3456', region: 'Austin', name: 'Austin Van 1' },
    { plate: 'NOP4567', region: 'Jacksonville', name: 'Jacksonville 1' },
    { plate: 'QRS5678', region: 'Fort Worth', name: 'Fort Worth 1' },
  ],
  // India - Format: MH12AB1234
  IN: [
    { plate: 'MH01AB1234', region: 'Mumbai', name: 'Mumbai Van 1' },
    { plate: 'MH02CD2345', region: 'Mumbai', name: 'Mumbai Van 2' },
    { plate: 'DL01EF3456', region: 'Delhi', name: 'Delhi Van 1' },
    { plate: 'DL02GH4567', region: 'Delhi', name: 'Delhi Van 2' },
    { plate: 'KA01IJ5678', region: 'Bangalore', name: 'Bangalore 1' },
    { plate: 'KA02KL6789', region: 'Bangalore', name: 'Bangalore 2' },
    { plate: 'TN01MN7890', region: 'Chennai', name: 'Chennai Van 1' },
    { plate: 'AP01OP8901', region: 'Hyderabad', name: 'Hyderabad 1' },
    { plate: 'GJ01QR9012', region: 'Ahmedabad', name: 'Ahmedabad 1' },
    { plate: 'WB01ST0123', region: 'Kolkata', name: 'Kolkata Van 1' },
    { plate: 'RJ01UV1234', region: 'Jaipur', name: 'Jaipur Van 1' },
    { plate: 'UP01WX2345', region: 'Lucknow', name: 'Lucknow Van 1' },
    { plate: 'MP01YZ3456', region: 'Bhopal', name: 'Bhopal Van 1' },
    { plate: 'PB01AB4567', region: 'Chandigarh', name: 'Chandigarh 1' },
    { plate: 'HR01CD5678', region: 'Gurugram', name: 'Gurgaon Van 1' },
  ],
  // Spain - Format: 1234 ABC
  ES: [
    { plate: '1234 ABC', region: 'Madrid', name: 'Madrid Van 1' },
    { plate: '2345 BCD', region: 'Madrid', name: 'Madrid Van 2' },
    { plate: '3456 CDE', region: 'Barcelona', name: 'Barcelona 1' },
    { plate: '4567 DEF', region: 'Barcelona', name: 'Barcelona 2' },
    { plate: '5678 EFG', region: 'Valencia', name: 'Valencia 1' },
    { plate: '6789 FGH', region: 'Seville', name: 'Sevilla Van 1' },
    { plate: '7890 GHI', region: 'Zaragoza', name: 'Zaragoza 1' },
    { plate: '8901 HIJ', region: 'Málaga', name: 'Málaga Van 1' },
    { plate: '9012 IJK', region: 'Murcia', name: 'Murcia Van 1' },
    { plate: '0123 JKL', region: 'Palma', name: 'Palma Van 1' },
    { plate: '1234 KLM', region: 'Bilbao', name: 'Bilbao Van 1' },
    { plate: '2345 LMN', region: 'Alicante', name: 'Alicante 1' },
    { plate: '3456 MNO', region: 'Córdoba', name: 'Córdoba Van 1' },
    { plate: '4567 NOP', region: 'Valladolid', name: 'Valladolid 1' },
    { plate: '5678 OPQ', region: 'Vigo', name: 'Vigo Van 1' },
  ],
};

// Current country code - can be set dynamically
let currentCountryCode = 'GB';

export function setVehicleCountry(countryCode: string) {
  currentCountryCode = countryCode;
}

export function getVehicleCountry(): string {
  return currentCountryCode;
}

/**
 * Get vehicle plate and name for a vehicle ID based on current country
 * Returns consistent plate for the same vehicle ID
 */
export function getVehiclePlate(vehicleId: number, countryCode?: string): { plate: string; region: string; name: string } {
  const country = countryCode || currentCountryCode;
  const plates = VEHICLE_PLATES_BY_COUNTRY[country] || VEHICLE_PLATES_BY_COUNTRY['GB'];
  return plates[vehicleId % plates.length];
}

/**
 * Format vehicle display name with country-appropriate plate
 * Example: "LN24 FLT" (UK), "AB-123-CD" (France)
 */
export function formatVehicleName(vehicleId: number, countryCode?: string): string {
  const vehicle = getVehiclePlate(vehicleId, countryCode);
  return `${vehicle.plate}`;
}

/**
 * Get full vehicle info string
 * Example: "LN24 FLT (Fleet Van 1 - London)"
 */
export function getVehicleDisplayName(vehicleId: number): string {
  const vehicle = getVehiclePlate(vehicleId);
  return `${vehicle.plate} (${vehicle.name})`;
}

// Generate vehicle colors
const VEHICLE_COLORS = [
  { color: '#76B900', stroke: '#5A8F00' }, // NVIDIA Green
  { color: '#006BBF', stroke: '#0052A5' }, // Accent Blue
  { color: '#F59E0B', stroke: '#D97706' }, // Warning Orange
  { color: '#EF4444', stroke: '#DC2626' }, // Red
  { color: '#8B5CF6', stroke: '#7C3AED' }, // Purple
  { color: '#EC4899', stroke: '#DB2777' }, // Pink
  { color: '#14B8A6', stroke: '#0D9488' }, // Teal
  { color: '#F97316', stroke: '#EA580C' }, // Orange
  { color: '#84CC16', stroke: '#65A30D' }, // Lime
  { color: '#06B6D4', stroke: '#0891B2' }, // Cyan
];

export function getVehicleColor(vehicleId: number): { color: string; stroke: string } {
  return VEHICLE_COLORS[vehicleId % VEHICLE_COLORS.length];
}

// Estimate payload size in MB
export function estimatePayloadSize(numStops: number): number {
  const n = numStops + 1; // +1 for depot
  return (43.2 * n * n) / (1024 * 1024);
}

// Check if payload exceeds 2GB limit
export function willExceedLimit(numStops: number): boolean {
  return estimatePayloadSize(numStops) > 2000;
}

// Recommend cluster count for large payloads
export function recommendClusterCount(numStops: number): number {
  const payloadMB = estimatePayloadSize(numStops);
  if (payloadMB <= 250) return 1;
  return Math.ceil(payloadMB / 250);
}
