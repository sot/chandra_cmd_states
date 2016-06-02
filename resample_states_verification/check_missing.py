from Chandra.Time import DateTime
for t in missing:
    t_match = np.interp(DateTime(t).secs, test['tstart'], test['pitch'])
    ref_match = official[official['datestart'] == t][0]['pitch']
    print t, ref_match - t_match
