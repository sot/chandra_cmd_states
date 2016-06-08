diffs = []
missing = []
for state in official[1:]:
    test_match = test['datestart'] == state['datestart']
    if np.any(test_match):
        pitch_match = test[test_match][0]['pitch']
        diffs.append(state['pitch'] - pitch_match)
        if np.abs(state['pitch'] - pitch_match) > 70:
            raise ValueError
    else:
        diffs.append(np.nan)
        missing.append(state['datestart'])
