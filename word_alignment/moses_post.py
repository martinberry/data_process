import cPickle
import gzip
import os


def extract(new, gz_path):
    with gzip.open(gz_path, 'r') as in_f:
        with open(new, 'w') as out_f:
            for line in in_f:
                line = line.strip('\r\n')
                if not line:
                    continue

                # print line

                line_frags = line.split('|||')
                if len(line_frags) < 3:
                    continue

                probs = line_frags[2].strip().split()

                out_line = '%s\t%s\t%s\n' % (line_frags[0].strip(), line_frags[1].strip(), probs[2])

                # print out_line

                out_f.write(out_line)


def add_len_col(new, old):
    with open(old, 'r') as i_f:
        with open(new, 'w') as o_f:
            counter = 0

            for line in i_f:
                counter += 1

                frags = line.strip().split('\t')
                src_len = len(frags[0].split())

                o_f.write('%d\t%s' % (src_len, line))

                if counter % 100000 == 0:
                    print counter


def pack(new, old, max_gram, min_prob):
    tmp_dict = {}
    with open(old, 'r') as f:
        with open(new, 'w') as of:
            counter = 0
            last_gram = 1
            tmp_dict[last_gram] = {}

            for line in f:
                counter += 1

                parsed = line.strip().split('\t')
                lw = parsed[1]
                rw = parsed[2]
                sc = float(parsed[3])

                lw_frags = lw.split()
                rw_frags = rw.split()

                if sc < min_prob:
                    continue

                curr_gram = len(lw_frags)

                if curr_gram != last_gram:
                    print '%d-gram: %d phrases founded' % (last_gram, len(tmp_dict[last_gram]))

                    for k, dt in tmp_dict[last_gram].iteritems():
                        of.write(k)
                        for align in dt:
                            of.write('\t')
                            of.write(align)
                        of.write('\n')

                    print '%d-gram saved' % last_gram

                    last_gram = curr_gram
                    if curr_gram > max_gram:
                        break
                    else:
                        tmp_dict[curr_gram] = {}

                new_aligned_words = set(rw_frags)
                if lw not in tmp_dict[curr_gram]:
                    aligned_words = new_aligned_words
                else:
                    aligned_words = tmp_dict[curr_gram][lw].union(new_aligned_words)

                sub_aligned_words = set()
                already_contained = False
                for gram in xrange(1, curr_gram):
                    for start in xrange(curr_gram - gram + 1):
                        sub = " ".join(lw_frags[start:start+gram])
                        if sub in tmp_dict[gram]:
                            sub_aligned_words = sub_aligned_words.union(tmp_dict[gram][sub])
                            if aligned_words.issubset(sub_aligned_words):
                                already_contained = True
                                break
                    if already_contained:
                        break
                if already_contained:
                    continue

                tmp_dict[curr_gram][lw] = aligned_words.difference(sub_aligned_words)

                if counter % 10000 == 0:
                    print counter

            if last_gram <= max_gram:
                print '%d-gram: %d phrases founded' % (last_gram, len(tmp_dict[last_gram]))

                for k, dt in tmp_dict[last_gram].iteritems():
                    of.write(k)
                    for align in dt:
                        of.write('\t')
                        of.write(align)
                    of.write('\n')

                print '%d-gram saved' % last_gram


def cat_1gram_and_mgram(new, unigram_path, mgram_path):
    with open(unigram_path, 'r') as u_f:
        with open(mgram_path, 'r') as m_f:
            with open(new, 'w') as f:
                for line in u_f:
                    f.write(line)

                last_is_m = False
                for line in m_f:
                    if not last_is_m:
                        line_frags = line.strip().split('\t')
                        if len(line_frags[0].split()) > 1:
                            last_is_m = True
                            f.write(line)
                    else:
                        f.write(line)


def to_pkl(pkl, file):
    align_dict = {}
    with open(file, 'r') as f:
        counter = 0

        for line in f:
            counter += 1

            line = line.strip()
            if not line:
                continue

            frags = line.split('\t')

            key = frags[0]
            align_dict[key] = frags[1:]

            if counter % 100000 == 0:
                print counter

    print 'saving lm dict file (format: word->[word1, word2...])'
    cPickle.dump(align_dict, open(pkl, 'w'))
    print 'saved in pickle'

## Step 1: extract phrase pair and the direct probability
extract('phrase-table.clean', 'phrase-table.gz')

## Step 2: add source phrase length column
add_len_col('phrase-table.clean.len', 'phrase-table.clean')

## Step 3: sort according to source phrase length
os.system('sort -n -k 1 phrase-table.clean.len > phrase-table.clean.len.sorted')

## Step 4: pack phrase table
pack('phrase-table.clean.len.sorted.pack_4gram-0', 'phrase-table.clean.len.sorted', 4, 0.)
pack('phrase-table.clean.len.sorted.pack_1gram-0.0001', 'phrase-table.clean.len.sorted', 1, 0.0001)

## Step 5: concat above phrase tables
cat_1gram_and_mgram('phrase-table.clean.len.sorted.pack_1gram-0.0001_mgram-0',
                    'phrase-table.clean.len.sorted.pack_1gram-0.0001', 'phrase-table.clean.len.sorted.pack_4gram-0')

## Step 6: convert to pkl
to_pkl('phrase-table.clean.len.sorted.pack_1gram-0.0001_mgram-0.pkl',
       'phrase-table.clean.len.sorted.pack_1gram-0.0001_mgram-0')
