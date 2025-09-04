function run_raptor(Ip0_arg, Major_radius_arg)
    close all hidden;
    run('/home/raptor/RAPTOR_path.m');  % Add RAPTOR path

    config = RAPTOR_config('ITER');  % Load default params
    config.init.Ip0 = Ip0_arg;  % Set Ip0 value
    config.equi.R0 = Major_radius_arg; % Set Major Radius value

    [model, params, init, g, v, U] = build_RAPTOR_model(config);  % Build model

    x0 = RAPTOR_initial_conditions(model, init, g(:, 1), v(:, 1));  % Initial conditions

    simres = RAPTOR_predictive(x0, g, v, U, model, params, 'verbosity', 2);  % Run simulation

    out = RAPTOR_out(simres, model, params);  % Compute outputs
    step_values = out.ti(1,:);
    final_value_current = step_values(end);

    % Previously both writematrix but changed to xlswrite to be compatible with Octave
    % Aaaand used to be appended but can do this in later or previous step
    csvwrite('step_values.txt', final_value_current);
    % csvwrite('out_time.txt', out.time);
end
