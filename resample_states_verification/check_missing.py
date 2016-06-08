from Chandra.Time import DateTime
equiv = []
for t in missing:
    t_match = np.interp(DateTime(t).secs, test['tstart'], test['pitch'])
    ref_match = official[official['datestart'] == t][0]['pitch']
    equiv.append(ref_match - t_match)

print "biggest offset is {}".format(np.max(np.abs(equiv)))
