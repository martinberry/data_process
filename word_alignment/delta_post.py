import cPickle


def get_diff(list1, list2):
    diff = []
    for item in list1:
        if item not in list2:
            diff.append(item)

    return diff


def update_align(update_align_pkl, old_align_pkl, new_align_pkl):
    old_align_dict = cPickle.load(open(old_align_pkl, 'r'))
    new_align_dict = cPickle.load(open(new_align_pkl, 'r'))
    update_align_dict = old_align_dict.copy()

    for k, new_aligns in new_align_dict.iteritems():
        if k in update_align_dict:
            print '==> update'
            print 'old: ', update_align_dict[k]
            print 'new: ', new_aligns

            diff = get_diff(new_aligns, update_align_dict[k])
            if len(diff):
                update_align_dict[k].extend(diff)

            print 'updated: ', update_align_dict[k]
        else:
            print '==> add'
            print 'new: ', new_aligns

            update_align_dict[k] = new_aligns

    cPickle.dump(update_align_dict, open(update_align_pkl, 'w'))


update_align('test.update.pkl', 'test.old.pkl', 'test.new.pkl')