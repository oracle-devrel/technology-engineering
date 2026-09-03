import { useState } from 'react';
import {
  Settings,
  Globe,
  MapPin,
  Building2,
  Truck,
  RotateCcw,
  Save,
  ChevronDown,
  ChevronRight,
  Check,
  Info,
} from 'lucide-react';
import { clsx } from 'clsx';
import { useConfigStore } from '@/store/configStore';
import { COUNTRIES, SCENARIO_PRESETS, getCountryByCode } from '@/data/locationData';
import { SUPPORTED_MODELS } from '@/api/genaiClient';

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultExpanded?: boolean;
}

function Section({ title, icon, children, defaultExpanded = true }: SectionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <div className="bg-dark-card rounded-xl border border-dark-border overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-dark-hover transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-oracle-red/10 flex items-center justify-center">
            {icon}
          </div>
          <span className="font-medium text-white">{title}</span>
        </div>
        {expanded ? (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-400" />
        )}
      </button>
      {expanded && <div className="px-4 pb-4 space-y-4">{children}</div>}
    </div>
  );
}

interface SelectFieldProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string; icon?: string }[];
  hint?: string;
}

function SelectField({ label, value, onChange, options, hint }: SelectFieldProps) {
  return (
    <div className="space-y-1">
      <label className="text-sm text-gray-400">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-oracle-red transition-colors"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.icon ? `${opt.icon} ` : ''}{opt.label}
          </option>
        ))}
      </select>
      {hint && <p className="text-xs text-gray-500">{hint}</p>}
    </div>
  );
}

interface NumberFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  hint?: string;
  unit?: string;
}

function NumberField({ label, value, onChange, min, max, step = 1, hint, unit }: NumberFieldProps) {
  return (
    <div className="space-y-1">
      <label className="text-sm text-gray-400">{label}</label>
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          min={min}
          max={max}
          step={step}
          className="flex-1 bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-oracle-red transition-colors"
        />
        {unit && <span className="text-gray-400 text-sm">{unit}</span>}
      </div>
      {hint && <p className="text-xs text-gray-500">{hint}</p>}
    </div>
  );
}

interface ToggleFieldProps {
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function ToggleField({ label, description, checked, onChange }: ToggleFieldProps) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <div className="text-sm text-white">{label}</div>
        {description && <div className="text-xs text-gray-500">{description}</div>}
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={clsx(
          'relative w-11 h-6 rounded-full transition-colors',
          checked ? 'bg-oracle-red' : 'bg-dark-border'
        )}
      >
        <div
          className={clsx(
            'absolute top-1 w-4 h-4 rounded-full bg-white transition-transform',
            checked ? 'left-6' : 'left-1'
          )}
        />
      </button>
    </div>
  );
}

interface RadioGroupProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}

function RadioGroup({ label, value, onChange, options }: RadioGroupProps) {
  return (
    <div className="space-y-2">
      <label className="text-sm text-gray-400">{label}</label>
      <div className="flex gap-4">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={clsx(
              'flex items-center gap-2 px-3 py-2 rounded-lg border transition-colors',
              value === opt.value
                ? 'border-oracle-red bg-oracle-red/10 text-oracle-red'
                : 'border-dark-border text-gray-400 hover:border-gray-500'
            )}
          >
            <div
              className={clsx(
                'w-4 h-4 rounded-full border-2 flex items-center justify-center',
                value === opt.value ? 'border-oracle-red' : 'border-gray-500'
              )}
            >
              {value === opt.value && <div className="w-2 h-2 rounded-full bg-oracle-red" />}
            </div>
            <span className="text-sm">{opt.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function AdminPage() {
  const {
    config,
    setCountry,
    setCity,
    setAiModel,
    setDistanceUnit,
    setTimeFormat,
    setVehicleLabelType,
    setDefaultVehicles,
    setDefaultShiftHours,
    setWorkingHours,
    setDefaultCenter,
    setDefaultZoom,
    setServiceRadius,
    setActiveScenario,
    setUseScenarioJobTypes,
    setUseScenarioRevenue,
    setUseScenarioMetrics,
    resetToDefaults,
  } = useConfigStore();

  const [saveStatus, setSaveStatus] = useState<'idle' | 'saved'>('idle');

  const selectedCountry = getCountryByCode(config.countryCode);
  const cities = selectedCountry?.cities || [];

  const handleSave = () => {
    // Config is auto-saved via persist middleware, but we show feedback
    setSaveStatus('saved');
    setTimeout(() => setSaveStatus('idle'), 2000);
  };

  const handleReset = () => {
    if (window.confirm('Are you sure you want to reset all settings to defaults?')) {
      resetToDefaults();
      setSaveStatus('saved');
      setTimeout(() => setSaveStatus('idle'), 2000);
    }
  };

  return (
    <div className="h-full overflow-auto bg-dark-bg p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-oracle-red flex items-center justify-center">
              <Settings className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Configuration Settings</h1>
              <p className="text-sm text-gray-400">
                Customize regional settings, defaults, and scenario options
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              Reset
            </button>
            <button
              onClick={handleSave}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
                saveStatus === 'saved'
                  ? 'bg-green-600 text-white'
                  : 'bg-oracle-red text-white hover:bg-oracle-red/90'
              )}
            >
              {saveStatus === 'saved' ? (
                <>
                  <Check className="w-4 h-4" />
                  Saved
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save
                </>
              )}
            </button>
          </div>
        </div>

        {/* Info Banner */}
        <div className="flex items-start gap-3 p-4 bg-oci-blue/10 border border-oci-blue/30 rounded-xl">
          <Info className="w-5 h-5 text-oci-blue shrink-0 mt-0.5" />
          <div className="text-sm text-gray-300">
            <p>
              Settings are automatically saved to your browser and will persist across sessions.
              Changing the country or city will update currency, units, and map defaults accordingly.
            </p>
          </div>
        </div>

        {/* Region Settings */}
        <Section
          title="Region Settings"
          icon={<Globe className="w-4 h-4 text-oracle-red" />}
        >
          <div className="grid grid-cols-2 gap-4">
            <SelectField
              label="Country"
              value={config.countryCode}
              onChange={setCountry}
              options={COUNTRIES.map((c) => ({
                value: c.code,
                label: c.name,
                icon: c.flag,
              }))}
              hint="Changing country updates currency and regional formats"
            />
            <SelectField
              label="City / Region"
              value={config.cityId}
              onChange={setCity}
              options={cities.map((c) => ({
                value: c.id,
                label: c.name,
              }))}
              hint="Sets default map center and service area"
            />
          </div>

          {/* AI Model Selection */}
          <SelectField
            label="AI Model"
            value={config.aiModel || 'openai.gpt-4o-mini'}
            onChange={setAiModel}
            options={SUPPORTED_MODELS.map((m) => ({
              value: m.id,
              label: `${m.name} (${m.provider})`,
            }))}
            hint="Select the AI model for route optimization analysis"
          />

          <div className="grid grid-cols-3 gap-4">
            <div className="p-3 bg-dark-bg rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Currency</div>
              <div className="text-lg font-semibold text-white">
                {config.currency.symbol} {config.currency.code}
              </div>
            </div>
            <div className="p-3 bg-dark-bg rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Date Format</div>
              <div className="text-lg font-semibold text-white">{config.dateFormat}</div>
            </div>
            <div className="p-3 bg-dark-bg rounded-lg">
              <div className="text-xs text-gray-500 mb-1">Timezone</div>
              <div className="text-lg font-semibold text-white">
                {cities.find((c) => c.id === config.cityId)?.timezone || 'UTC'}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <RadioGroup
              label="Distance Units"
              value={config.distanceUnit}
              onChange={(v) => setDistanceUnit(v as 'km' | 'miles')}
              options={[
                { value: 'km', label: 'Kilometers' },
                { value: 'miles', label: 'Miles' },
              ]}
            />
            <RadioGroup
              label="Time Format"
              value={config.timeFormat}
              onChange={(v) => setTimeFormat(v as '12h' | '24h')}
              options={[
                { value: '24h', label: '24-hour' },
                { value: '12h', label: '12-hour' },
              ]}
            />
          </div>
        </Section>

        {/* Map Defaults */}
        <Section
          title="Map Defaults"
          icon={<MapPin className="w-4 h-4 text-oracle-red" />}
        >
          <div className="grid grid-cols-2 gap-4">
            <NumberField
              label="Default Latitude"
              value={config.defaultCenter.lat}
              onChange={(v) => setDefaultCenter(v, config.defaultCenter.lng)}
              step={0.0001}
              hint="Center point latitude"
            />
            <NumberField
              label="Default Longitude"
              value={config.defaultCenter.lng}
              onChange={(v) => setDefaultCenter(config.defaultCenter.lat, v)}
              step={0.0001}
              hint="Center point longitude"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <NumberField
              label="Default Zoom Level"
              value={config.defaultZoom}
              onChange={setDefaultZoom}
              min={1}
              max={20}
              hint="Map zoom level (1-20)"
            />
            <NumberField
              label="Service Radius"
              value={config.serviceRadius}
              onChange={setServiceRadius}
              min={5}
              max={200}
              unit="km"
              hint="Default service area radius"
            />
          </div>
        </Section>

        {/* Business Defaults */}
        <Section
          title="Business Defaults"
          icon={<Building2 className="w-4 h-4 text-oracle-red" />}
        >
          <div className="grid grid-cols-2 gap-4">
            <NumberField
              label="Default Vehicles"
              value={config.defaultVehicles}
              onChange={setDefaultVehicles}
              min={1}
              max={100}
              hint="Number of vehicles/technicians"
            />
            <NumberField
              label="Shift Duration"
              value={config.defaultShiftHours}
              onChange={setDefaultShiftHours}
              min={4}
              max={12}
              step={0.5}
              unit="hours"
              hint="Default shift length"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm text-gray-400">Working Hours Start</label>
              <input
                type="time"
                value={config.workingHoursStart}
                onChange={(e) => setWorkingHours(e.target.value, config.workingHoursEnd)}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-oracle-red transition-colors"
              />
            </div>
            <div className="space-y-1">
              <label className="text-sm text-gray-400">Working Hours End</label>
              <input
                type="time"
                value={config.workingHoursEnd}
                onChange={(e) => setWorkingHours(config.workingHoursStart, e.target.value)}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2 text-white focus:outline-none focus:border-oracle-red transition-colors"
              />
            </div>
          </div>
          <RadioGroup
            label="Vehicle Labels"
            value={config.vehicleLabelType}
            onChange={(v) => setVehicleLabelType(v as 'generic' | 'license_plate')}
            options={[
              { value: 'generic', label: 'Generic (Vehicle 1, 2...)' },
              { value: 'license_plate', label: `License Plates (${selectedCountry?.licensePlateExample || 'ABC123'})` },
            ]}
          />
        </Section>

        {/* Scenario Presets */}
        <Section
          title="Scenario Presets"
          icon={<Truck className="w-4 h-4 text-oracle-red" />}
        >
          <SelectField
            label="Active Scenario"
            value={config.activeScenario}
            onChange={setActiveScenario}
            options={SCENARIO_PRESETS.map((s) => ({
              value: s.id,
              label: s.name,
            }))}
            hint="Select industry-specific configuration"
          />

          {config.activeScenario === 'belron' && (
            <div className="p-4 bg-dark-bg rounded-lg space-y-3">
              <div className="text-sm font-medium text-white">Belron Job Types</div>
              <div className="grid grid-cols-3 gap-3">
                {config.scenarioJobTypes.map((jt) => (
                  <div
                    key={jt.id}
                    className="p-3 rounded-lg border border-dark-border"
                    style={{ borderLeftColor: jt.color, borderLeftWidth: 3 }}
                  >
                    <div className="font-medium text-white text-sm">{jt.label}</div>
                    <div className="text-xs text-gray-400 mt-1">
                      {jt.duration} min | {config.currency.symbol}{jt.revenue}
                    </div>
                    <div className="text-xs text-gray-500">
                      Default: {jt.defaultPercentage}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="space-y-2 border-t border-dark-border pt-4">
            <ToggleField
              label="Use Scenario Job Types"
              description="Replace generic job types with scenario-specific types"
              checked={config.useScenarioJobTypes}
              onChange={setUseScenarioJobTypes}
            />
            <ToggleField
              label="Use Scenario Revenue Values"
              description="Apply scenario-specific pricing in calculations"
              checked={config.useScenarioRevenue}
              onChange={setUseScenarioRevenue}
            />
            <ToggleField
              label="Use Scenario Business Metrics"
              description="Show industry-specific KPIs and impact metrics"
              checked={config.useScenarioMetrics}
              onChange={setUseScenarioMetrics}
            />
          </div>
        </Section>

        {/* Current Configuration Summary */}
        <div className="p-4 bg-dark-card rounded-xl border border-dark-border">
          <div className="text-sm font-medium text-gray-400 mb-3">Current Configuration Summary</div>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <div className="text-gray-500">Region</div>
              <div className="text-white font-medium">
                {selectedCountry?.flag} {selectedCountry?.name}
              </div>
            </div>
            <div>
              <div className="text-gray-500">City</div>
              <div className="text-white font-medium">
                {cities.find((c) => c.id === config.cityId)?.name}
              </div>
            </div>
            <div>
              <div className="text-gray-500">Scenario</div>
              <div className="text-white font-medium">
                {SCENARIO_PRESETS.find((s) => s.id === config.activeScenario)?.name}
              </div>
            </div>
            <div>
              <div className="text-gray-500">Fleet Size</div>
              <div className="text-white font-medium">
                {config.defaultVehicles} vehicles
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-gray-500 pb-4">
          Configuration v1.0 | Settings stored in browser localStorage
        </div>
      </div>
    </div>
  );
}

export default AdminPage;
