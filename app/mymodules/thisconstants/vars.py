#DATA

MONTHS_SPANISH = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

STATIC_DATA = ['employee_code', 'username', 'names', 'hire_date']
MUTABLE_DATA = ['region', 'zone', 'agency', 'committee', 'category']

"""R327_COLS = ['type', 'worked_days', 'sadc', 'sadm', 'sadp', 'sbs', 'vacbc', 'vacbm', 
    'vmcbc', 'vmcbm', 'vdcbc', 'vdcbm', 'damnn', 'damnm', 'damrn', 'damrm', 'damtn', 'damtm',
    'dammm', 'damm_', 'dam_tea', 'cccds', 'cccd_', 'ccm1_8s', 'ccm1_8_', 'ccm9_30s',
    'ccm9_30_', 'ccm30s', 'ccm30_', 'ccm8s', 'ccm8_', 'ccm8cvs', 'ccm8cv_', 'ccvm8cvs', 'ccvm8cv_',
    'ccvm30cvs', 'ccvm30cv_', 't1_30bac', 't1_30cc', 't1_30cd', 't1_30mc_', 't_1_60bac', 
    't_1_60cc',  't_1_60cd',  't_1_60mc_',  'smeta',  'slmen_',  'cmeta',  'clmen_',  
    'mcmeta',  'mcl_',  'rcnb',  'rcnr',  'rcr_',  'rcavnb',  'rcavnr',
    'rcavr_',  'spnppm',  'spnppd','spnpeh','spph_',  'growth_s', 'growth_c',
    'retention', 'cont31_60', 'cartm_8', 'productivity', 'score', 'quali']"""

R327_NEEDED_COLS = ['worked_days', 'sadc', 'sadm', 'sbs', 'vmcbc', 'vmcbm', 'smeta', 'cmeta',
                    'retention', 'spph_', 'score', 'quali']

"""R017_COLS = ['kpi_top', 'kpi_pu', 'kpi_mpu6m', 'edspme',
 'eds_', 'odnoni', 'odnoni_', 'odnor', 'odnor_', 'odvodc', 'odvodc_', 'no1', 'no2', 'no3', 'no4', 
 'no5', 'no6', 'no7', 'no8', 'no9', 'no10', 'no11', 'no12', 'no13', 'no14', 'no15', 'no16', 'no17', 
 'no18', 'no19', 'no20', 'no21', 'no22', 'no23', 'no24', 'no25', 'no26', 'no27', 'no28', 'no29', 
 'no30', 'no31', 'donton', 'doncpa', 'doncpaldp', 'doncpoo', 'donncp_reprog', 'donncp_refin',
 'donncp_pren', 'donncp_rpren', 'donncp_odldp', 'mdo_kpi_top', 'mdo_kpi_pu', 'mdo_kpi_mpu6m', 'mdo_edspme',
 'mdo_eds_', 'mdo_odnoni', 'mdo_odnoni_', 'mdo_odnor', 'mdo_odnor_', 'mdo_odvodc', 'mdo_odvodc_', 'dostos',
 'doscpa', 'doscpaldp', 'doscpoo', 'dosncp_reprog', 'dosncp_refin', 'dosncp_pren', 'dosncp_rpren', 
 'dosncp_odldp']"""

R017_NEEDED_COLS = ['kpi_top']

import pandas as pd

QUALI_LOOKUP = pd.DataFrame({
    'min_value': [-1000, 10, 46, 82],
    'max_value': [9.99, 45.99, 81.99, 1000],
    'description': ['MALO', 'REGULAR', 'BUENO', 'MUY BUENO']
})
