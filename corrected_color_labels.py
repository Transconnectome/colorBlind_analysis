
# Color hue definitions (Lab hue angles in degrees)

# TEST subjects (sub-01, 02, 03, 04): Regular 45° spacing
LABEL2HUE_DEG_TEST = {
    'color_1': 180.0,   # Red
    'color_2': 225.0,   # Orange
    'color_3': 270.0,   # Yellow
    'color_4': 315.0,   # Greenish
    'color_5': 0.0,     # Cyan
    'color_6': 45.0,    # Blue
    'color_7': 90.0,    # Violet
    'color_8': 135.0,   # Pinkish
}

# PILOT subject (sub-P01): Measured irregular spacing
LABEL2HUE_DEG_PILOT = {
    'color_1': 182.14,
    'color_2': 287.98,
    'color_3': 305.23,
    'color_4': 330.20,
    'color_5': 35.27,
    'color_6': 73.37,
    'color_7': 125.59,
    'color_8': 143.91,
}

def get_label2hue_for_subject(subject_id):
    """
    Return appropriate LABEL2HUE_DEG based on subject

    Parameters:
    -----------
    subject_id : str
        Subject ID (e.g., '01', '02', 'P01')

    Returns:
    --------
    dict : LABEL2HUE_DEG_TEST or LABEL2HUE_DEG_PILOT
    """
    if subject_id.startswith('P'):
        return LABEL2HUE_DEG_PILOT
    else:
        return LABEL2HUE_DEG_TEST

# Usage in analysis script:
# LABEL2HUE_DEG = get_label2hue_for_subject(SUBJECT_ID)
#
# Then use LABEL2HUE_DEG throughout instead of hardcoded LABEL2HUE_DEG_PILOT
