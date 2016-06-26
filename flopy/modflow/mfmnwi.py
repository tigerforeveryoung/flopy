import sys
from ..pakbase import Package
from flopy.utils.flopy_io import line_parse, pop_item

class ModflowMnwi(Package):
    """
    'Multi-Node Well Information Package Class'

    Parameters
    ----------
    model : model object
        The model object (of type :class:`flopy.modflow.mf.Modflow`) to which
        this package will be added.
    wel1flag : integer
        Flag indicating output to be written for each MNW node at the end of each stress period
    qsumflag :integer
        Flag indicating output to be written for each multi-node well
    byndflag :integer
        Flag indicating output to be written for each MNW node
    mnwobs :integer
        Number of multi-node wells for which detailed flow, head, and solute data re to be saved
    wellid_unit_qndflag_qhbflag_concflag : list of lists
        Containing wells and related information to be output (length : [MNWOBS][4or5])
    extension : string
        Filename extension (default is 'mnwi')
    unitnumber : int
        File unit number (default is 58).

    Attributes
    ----------

    Methods
    -------

    See Also
    --------

    Notes
    -----

    Examples
    --------

    >>> import flopy
    >>> ml = flopy.modflow.Modflow()
    >>> ghb = flopy.modflow.ModflowMnwi(ml, ...)

    """

    def __init__(self, model, wel1flag=1, qsumflag=1, byndflag=1, mnwobs=1, wellid_unit_qndflag_qhbflag_concflag=None,
                 extension='mnwi', unitnumber=58):
        Package.__init__(self, model, extension, 'MNWI',
                         unitnumber)  # Call ancestor's init to set self.parent, extension, name, and unit number
        self.url = 'mnwi.htm'
        self.heading = '# Multi-node well information (MNWI) file for MODFLOW, generated by Flopy'
        self.wel1flag = wel1flag  # -integer flag indicating output to be written for each MNW node at the end of each stress period
        self.qsumflag = qsumflag  # -integer flag indicating output to be written for each multi-node well
        self.byndflag = byndflag  # -integer flag indicating output to be written for each MNW node
        self.mnwobs = mnwobs  # -number of multi-node wells for which detailed flow, head, and solute data re to be saved
        self.wellid_unit_qndflag_qhbflag_concflag = wellid_unit_qndflag_qhbflag_concflag  # -list of lists containing wells and related information to be output (length = [MNWOBS][4or5])

        # -input format checks:
        assert self.wel1flag >= 0, 'WEL1flag must be greater than or equal to zero.'
        assert self.qsumflag >= 0, 'QSUMflag must be greater than or equal to zero.'
        assert self.byndflag >= 0, 'BYNDflag must be greater than or equal to zero.'

        if len(self.wellid_unit_qndflag_qhbflag_concflag) != self.mnwobs:
            print('WARNING: number of listed well ids to be monitored does not match MNWOBS.')

        self.parent.add_package(self)

    @staticmethod
    def load(f, model, nper=None, gwt=False, nsol=1, ext_unit_dict=None):

        if model.verbose:
            sys.stdout.write('loading mnw2 package file...\n')

        structured = model.structured
        if nper is None:
            nrow, ncol, nlay, nper = model.get_nrow_ncol_nlay_nper()
            nper = 1 if nper == 0 else nper  # otherwise iterations from 0, nper won't run

        if not hasattr(f, 'read'):
            filename = f
            f = open(filename, 'r')

        # dataset 1
        line = line_parse(next(f))
        wel1flag, qsumflag, byndflag = map(int, line)

        # dataset 2
        mnwobs = pop_item(line_parse(next(f)))
        wellid_unit_qndflag_qhbflag_concflag = []
        if mnwobs > 0:
            for i in range(mnwobs):
                # dataset 3
                line = line_parse(next(f))
                wellid = pop_item(line, str)
                unit = pop_item(line, int)
                qndflag = pop_item(line, int)
                qbhflag = pop_item(line, int)
                tmp = [wellid, unit, qndflag, qbhflag]
                if gwt and len(line) > 0:
                    tmp.append(pop_item(line, int))
                wellid_unit_qndflag_qhbflag_concflag.append(tmp)
        return ModflowMnwi(model, wel1flag=wel1flag, qsumflag=qsumflag, byndflag=byndflag, mnwobs=mnwobs,
                           wellid_unit_qndflag_qhbflag_concflag=wellid_unit_qndflag_qhbflag_concflag,
                           extension='mnwi', unitnumber=58)


    def write_file(self):
        """
        Write the package file.

        Returns
        -------
        None

        """

        # -open file for writing
        f_mnwi = open(self.file_name[0], 'w')

        # -write header
        f_mnwi.write('%s\n' % self.heading)

        # -Section 1 - WEL1flag QSUMflag SYNDflag
        f_mnwi.write('%10i%10i%10i\n' % (self.wel1flag, self.qsumflag, self.byndflag))

        # -Section 2 - MNWOBS
        f_mnwi.write('%10i\n' % self.mnwobs)

        # -Section 3 - WELLID UNIT QNDflag QBHflag {CONCflag} (Repeat MNWOBS times)
        for i in range(self.mnwobs):
            wellid = self.wellid_unit_qndflag_qhbflag_concflag[i][0]
            unit = self.wellid_unit_qndflag_qhbflag_concflag[i][1]
            qndflag = self.wellid_unit_qndflag_qhbflag_concflag[i][2]
            qhbflag = self.wellid_unit_qndflag_qhbflag_concflag[i][3]
            assert qndflag >= 0, 'QNDflag must be greater than or equal to zero.'
            assert qhbflag >= 0, 'QHBflag must be greater than or equal to zero.'
            if len(self.wellid_unit_qndflag_qhbflag_concflag[i]) == 4:
                f_mnwi.write('%s %2i%10i%10i\n' % (wellid, unit, qndflag, qhbflag))
            elif len(self.wellid_unit_qndflag_qhbflag_concflag[i]) == 5:
                concflag = self.wellid_unit_qndflag_qhbflag_concflag[i][4]
                assert 0 <= concflag <= 3, 'CONCflag must be an integer between 0 and 3.'
                assert isinstance(concflag, int), 'CONCflag must be an integer between 0 and 3.'
                f_mnwi.write('%s %2i%10i%10i%10i\n' % (wellid, unit, qndflag, qhbflag, concflag))

        f_mnwi.close()
