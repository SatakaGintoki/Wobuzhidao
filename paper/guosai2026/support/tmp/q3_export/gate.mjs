export const requiredChecks = [
  'event_found', 'finite', 'strict_below_all_verified_grids',
  'strict_below_with_empirical_margin', 'moisture_bounds', 'temperature_bounds',
  'moisture_balance_1e-6', 'heat_balance_1e-6', 'quadrature_convergence_1e-7',
  'space_event_60s', 'time_event_60s', 'space_full_fields_2e-5',
  'time_full_fields_2e-5', 'table_four_decimals', 'q2_overlap',
];

export function requireQ3Delivery(v) {
  const gate = v?.delivery_gate;
  if (v?.result_version !== 'q3-closeout-v1' || gate?.meets_delivery_gate !== true ||
      !requiredChecks.every(name => gate?.checks?.[name] === true) ||
      !Object.values(gate.checks).every(value => value === true)) {
    throw new Error('Numerical validation failed. Q3 export blocked.');
  }
}
