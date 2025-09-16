#
# Single block thermal input with time derivative term
# https://mooseframework.inl.gov/modules/heat_transfer/tutorials/introduction/therm_step03.html
#

[Mesh]
  file = mesh_2d.e
[]

[Functions]
  [./left_val]
    type = PiecewiseLinear
    x = '250.0 260.0'
    y = yl1 yl2
  [../]
  [./mid_val]
    type = PiecewiseLinear
    x = '250.0 260.0'
    y = ym1 ym2
  [../]
  [./right_val]
    type = PiecewiseLinear
    x = '250.0 260.0'
    y = yr1 yr2
  [../]

  [./temp_profile]
    type = ParsedFunction
    expression = 'if(x < -230.5, 20 + (left - 20) * (3 * ((x + 357)/126.5)^2 - 2 * ((x + 357)/126.5)^3), if(x < -130.5, left, if(x < -90.5, left + (mid - left) * (3 * ((x + 130.5)/40)^2 - 2 * ((x + 130.5)/40)^3), if(x < 9.5, mid, if(x < 49.5, mid + (right - mid) * (3 * ((x - 9.5)/40)^2 - 2 * ((x - 9.5)/40)^3), if(x < 149.5, right, right + (20 - right) * (3 * ((x - 149.5)/126.5)^2 - 2 * ((x - 149.5)/126.5)^3)))))))'
    symbol_names = 'left mid right'
    symbol_values = 'left_val mid_val right_val'
  [../]
[]


[Kernels]
  [heat_conduction]
    type = ADDiffusion
    variable = temperature
  []

  [transient_term]
    type = ADHeatConductionTimeDerivative
    variable = temperature
  []
[]

[Variables]
  [temperature]
    order = FIRST
    family = LAGRANGE
    initial_condition = 20.0
  []
[]

[Materials]
  [thermal]
    type = ADGenericConstantMaterial
    prop_names = 'thermal_conductivity specific_heat density'
    prop_values = '0.018 500 8e-6'
  []
[]

[BCs]

  [./middle_temp_bc]
    type = FunctionDirichletBC
    boundary = 'outer'                   
    variable = temperature                   
    function = temp_profile             
  [../]

  [./side_outer_conv_bc]
    type = ConvectiveFluxFunction
    variable = temperature
    boundary = 'outer_side'
    coefficient = 20
    T_infinity = 20
  [../]

  [./side_outer_rad_bc]
    type = FunctionRadiativeBC
    variable = temperature
    boundary = 'outer_side'
    emissivity_function = 0.3
    Tinfinity = 20
  [../]

[]

[ThermalContact]
  [left_gap_contact]
    type = GapHeatTransfer
    variable = temperature
    primary = 'left_top'
    secondary = 'left_bottom'
    gap_conductance = 200
    emissivity_primary = 0.0
    emissivity_secondary = 0.0
    quadrature = true
  []
  [right_gap_contact]
    type = GapHeatTransfer
    variable = temperature
    primary = 'right_top'
    secondary = 'right_bottom'
    gap_conductance = 200
    emissivity_primary = 0.0
    emissivity_secondary = 0.0
    quadrature = true
  []
  
[]


[Executioner]
  type = Transient
  solve_type = 'NEWTON'
  start_time = 250.0
  end_time = 260.0
  dt = 2.0            
[]


[Outputs]
  [./vtk]
    type = VTK
    file_base = TP_index
  [../]
  [./restart_out]
    type = Checkpoint
    file_base = restart
    num_files = 1
    time_step_interval = 1
  [../]
[]