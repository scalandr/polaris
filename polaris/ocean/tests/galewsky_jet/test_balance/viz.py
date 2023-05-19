import cmocean  # noqa: F401
import xarray as xr

from polaris import Step
from polaris.remap import MappingFileStep
from polaris.viz.globe import plot_global


class VizMap(MappingFileStep):
    """
    A step for making a mapping file for galewsky jet viz

    Attributes
    ----------
    mesh_name : str
        The name of the mesh
    """
    def __init__(self, test_case, name, subdir, mesh_name):
        """
        Create the step

        Parameters
        ----------
        test_case : polaris.TestCase
            The test case this step belongs to

        name : str
            The name of the step

        subdir : str
            The subdirectory in the test case's work directory
            for the step

        mesh_name : str
            The name of the mesh
        """
        super().__init__(test_case=test_case, name=name, subdir=subdir,
                         ntasks=128, min_tasks=1)
        self.mesh_name = mesh_name
        self.add_input_file(filename='mesh.nc',
                            target='../base_mesh/mesh.nc')

    def run(self):
        """
        Set up the source and destination grids for this step
        """
        config = self.config
        section = config['galewsky_jet_vizmap']
        dlon = section.getfloat('dlon')
        dlat = section.getfloat('dlat')
        method = section.get('remap_method')
        self.src_from_mpas(filename='mesh.nc', mesh_name=self.mesh_name)
        self.dst_global_lon_lat(dlon=dlon, dlat=dlat)
        self.method = method

        super().run()


class Viz(Step):
    """
    A step for plotting fields from the galewsky jet output

    Attributes
    ----------
    mesh_name : str
        The name of the mesh
    """
    def __init__(self, test_case, name, subdir, viz_map, mesh_name):
        """
        Create the step

        Parameters
        ----------
        test_case : polaris.TestCase
            The test case this step belongs to

        name : str
            The name of the step

        subdir : str
            The subdirectory in the test case's work directory for the step

        viz_map : polaris.ocean.tests.galewsky_jet.test_balance.viz.VizMap
            The step for creating a mapping files, also used to remap data
            from the MPAS mesh to a lon-lat grid

        mesh_name : str
            The name of the mesh
        """
        super().__init__(test_case=test_case, name=name, subdir=subdir)
        self.add_input_file(
            filename='initial_state.nc',
            target='../initial_state/initial_state.nc')
        self.add_input_file(
            filename='output.nc',
            target='../forward/output.nc')
        self.add_dependency(viz_map, name='viz_map')
        self.mesh_name = mesh_name
        self.add_output_file('init.png')
        self.add_output_file('final.png')

    def run(self):
        """
        Run this step of the test case
        """
        config = self.config
        mesh_name = self.mesh_name

        viz_map = self.dependencies['viz_map']

        remapper = viz_map.get_remapper()

        ds_init = xr.open_dataset('initial_state.nc')
        ds_init = ds_init[['layerThickness', ]].isel(Time=0, nVertLevels=0)
        ds_init = remapper.remap(ds_init)

        plot_global(ds_init.lon.values, ds_init.lat.values,
                    ds_init.layerThickness.values,
                    out_filename='init.png', config=config,
                    colormap_section='galewsky_jet_viz_thickness',
                    title=f'{mesh_name} layerThickness at init',
                          plot_land=False)

        ds_out = xr.open_dataset('output.nc')
        ds_out = ds_out[['layerThickness', ]].isel(Time=-1, nVertLevels=0)
        ds_out = remapper.remap(ds_out)

        plot_global(ds_out.lon.values, ds_out.lat.values,
                    ds_out.layerThickness.values,
                    out_filename='final.png', config=config,
                    colormap_section='galewsky_jet_viz_thickness',
                    title=f'{mesh_name} layerThickness at end of run',
                    plot_land=False)

        ds_out = xr.open_dataset('output.nc')
        ds_out = ds_out[['kineticEnergyCell', ]].isel(Time=-1, nVertLevels=0)
        ds_out = remapper.remap(ds_out)

        plot_global(ds_out.lon.values, ds_out.lat.values,
                    ds_out.kineticEnergyCell.values,
                    out_filename='final_ke.png', config=config,
                    colormap_section='galewsky_jet_viz_kineticenergy',
                    title=f'{mesh_name} kinetic energy at end of run',
                    plot_land=False)
