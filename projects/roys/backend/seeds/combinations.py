COMBINATIONS = [
    {
        "combo_key": "21_CFR_820",
        "name": "FDA QSR Only",
        "description": "US FDA Quality System Regulation standalone",
        "standard_codes": ["21_CFR_820"],
    },
    {
        "combo_key": "ISO_13485",
        "name": "ISO 13485 Only",
        "description": "ISO 13485 Quality Management standalone",
        "standard_codes": ["ISO_13485"],
    },
    {
        "combo_key": "EU_MDR",
        "name": "EU MDR Only",
        "description": "European Medical Device Regulation standalone",
        "standard_codes": ["EU_MDR"],
    },
    {
        "combo_key": "21_CFR_820+ISO_13485",
        "name": "FDA + ISO 13485",
        "description": "Combined FDA QSR and ISO 13485 compliance — most common combo for US medical device companies",
        "standard_codes": ["21_CFR_820", "ISO_13485"],
    },
    {
        "combo_key": "21_CFR_820+EU_MDR+ISO_13485",
        "name": "FDA + ISO 13485 + EU MDR",
        "description": "Full international compliance — US + EU markets",
        "standard_codes": ["21_CFR_820", "EU_MDR", "ISO_13485"],
    },
    {
        "combo_key": "21_CFR_58+ISO_17025",
        "name": "GLP + ISO 17025",
        "description": "Laboratory compliance combo — FDA GLP and ISO testing/calibration",
        "standard_codes": ["21_CFR_58", "ISO_17025"],
    },
]
