solubility = 4e-2 # mol/m^3/Pa^0.5
diffusivity = 1.5e-9 # m^2/s
temperature = 773.15 # K
V_chamber = 3.278e-5 # m^3 (3.278e-4 m^3)
pressure_inlet = 42000.0 # Pa
simulation_time = 10.0 # s
interval_time = 5 # s
R_gas = 8.314 # J/(mol*K)

[Functions]
  [concentration_factor_inlet]
    type = ParsedFunction
    expression = '${solubility} * sqrt(${pressure_inlet})'
  []

  [concentration_factor_outlet]
    type = ParsedFunction
    expression = '${solubility} * sqrt(p_out_dynamic)'
    symbol_names  = 'p_out_dynamic'
    symbol_values  = 'p_out_dynamic'
  []
[]

[Mesh]
  file = mesh.msh
[]

[Problem]
  type = ReferenceResidualProblem
  extra_tag_vectors = 'ref'
  reference_vector = 'ref'
[]

[Variables]
  [mobile]
  []
[]

[Kernels]
  [diff]
    type = Diffusion
    variable = mobile
    extra_vector_tags = ref
  []
  [time]
    type = TimeDerivative
    variable = mobile
    extra_vector_tags = ref
  []
[]

[BCs]
  [left]
    type = FunctionDirichletBC
    variable = mobile
    function = concentration_factor_inlet
    boundary = left
  []
  [right]
    type = FunctionDirichletBC
    variable = mobile
    function = concentration_factor_outlet
    boundary = right
  []
[]

[Postprocessors]
  [outflux_mol]
    type = SideDiffusiveFluxAverage
    boundary = 'right'
    diffusivity=${diffusivity}
    variable = mobile
    execute_on = 'TIMESTEP_END'
  []

  [n_gas]
    type = TimeIntegratedPostprocessor
    value = outflux_mol 
  []

  [p_out_dynamic]
    type = ParsedPostprocessor
    pp_names = 'n_gas'
    expression = '(n_gas * ${R_gas} * ${temperature}) / ${V_chamber}'
    execute_on = 'TIMESTEP_END'
  []
[]

[Preconditioning]
  [smp]
    type = SMP
    full = true
  []
[]

[Executioner]
  type = Transient
  end_time = ${simulation_time}
  dt = ${interval_time}
  solve_type = NEWTON
  scheme = BDF2
  nl_abs_tol = 1e-13
  petsc_options_iname = '-pc_type'
  petsc_options_value = 'lu'
  automatic_scaling = true
  verbose = true
  compute_scaling_once = false
[]

#[Outputs]
#  exodus = true
#  csv = true
#[]

[Outputs]
  csv = true
  [./vtk]
    type = VTK
    file_base = 'diffusion'
  [../]
[]
