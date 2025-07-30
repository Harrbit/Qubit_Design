from qiskit_metal.analyses.quantization import EPRanalysis

def epr_components(comp_list:list, design, options:dict, simulation_name:str="sim", output_mode:int=0):
    """
    Conduct EPR (energy participation ratio) simulation for any one or more components.

    Args:
        comp_list (list[str]): the list of the names of components submitted for simulation
        design (DesignPlanar): the design in which the components are, it should be a DesignPlanar class from qiskit_metal.designs.design_planar.DesignPlanar
        options (Dict): options for the simulation, the dictionary is structured as follows
            {
                "max_passes":int,
                "vars":Dict{
                    "Lj":str,
                }
                "setup_update":Dict{
                    "max_delta_f": float,
                    "min_freq_ghz": float,
                }
                "sim_run_options":Dict{
                    "open_terminations":list[tuple(str,str)],
                    "port_list": list[tuple(str,str)],
                }
            }
        output_mode (int): the amount of output needed, 0=no output, 1=full output, 2= figure only, 3=text only
    """
    eig_qd = EPRanalysis(design, "hfss")
    eig_qd.setup.maxpasses = options["max_passes"]
    eig_qd.sim.setup.vars.Lj = options["vars"]["Lj"]
    eig_qd.sim.setup_update(max_delta_f = options["setup_update"]["max_delta_f"],
                            min_freq_ghz = options["setup_update"]["min_freq_ghz"],
                            n_modes = options["setup_update"]["n_modes"])

    eig_qd.sim.run(name=simulation_name, 
                   components=comp_list, 
                   open_terminations=options["sim_run_options"]["open_terminations"], 
                   port_list=options["sim_run_options"]["port_list"])
    
    if output_mode == 1 or output_mode == 2:
        eig_qd.sim.plot_convergences()

    eig_qd.setup.junctions.jj.rect = f'JJ_rect_Lj_{comp_list[0]}_rect_jj'
    eig_qd.setup.junctions.jj.line = f'JJ_Lj_{comp_list[0]}_rect_jj_'

    if output_mode == 1 or output_mode == 3:
        print("Simulator set up:\n",eig_qd.sim.setup)
    
    eig_qd.run_epr()
    return eig_qd.sim.renderer.epr_quantum_analysis.results