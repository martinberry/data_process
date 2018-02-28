#encoding=utf-8
import sys
import os
import codecs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import rule_engine
from Bifrost.bifrost import Bifrost
from BPE.subword_nmt.apply_bpe import BPE
from rule_common import General_Sentence_Tokenizer, Remove_Add_Line_Char

tok_data_zh = ["现将修改后的《中小企业信用担保资金管理办法》印发给你们，请遵照执行。",
               "三十九、第五十三条改为第六十条，删去第一款；第二款作为第一款；第三款作为第二款，修改为:“省?{]|、自治区、直辖市人民代表大会常务委员会可以根据本法制定实施办法“。",
               "第十二条　专业清洗机构从事二次供水设施的清洗消毒，应与二次供水设施的管理机构签订《二次供水设施清洗消毒合同》。",
               "为?“省、自治区、直辖市人民代表大会常务委员会可以根据本法制定实施办法"]
exp_tok = '''现将修改后的 《 中小企业信用担保资金管理办法 》 印发给你们 ， 请遵照执行 。
三十九 、 第五十三条改为第六十条 ， 删去第一款 ； 第二款作为第一款 ； 第三款作为第二款 ， 修改为 : “ 省 ? { &#93; &#124; 、 自治区 、 直辖市人民代表大会常务委员会可以根据本法制定实施办法 “ 。
第十二条 专业清洗机构从事二次供水设施的清洗消毒 ， 应与二次供水设施的管理机构签订 《 二次供水设施清洗消毒合同 》 。
为 ? “ 省 、 自治区 、 直辖市人民代表大会常务委员会可以根据本法制定实施办法'''
def test_General_Sentence_Tokenizer():
    general_tok = General_Sentence_Tokenizer(lang = 'zh')
    res_zh = []
    for line in tok_data_zh:
        res = general_tok.run(line)
        res_zh.append(res)
    assert '\n'.join(res_zh) == exp_tok
test_General_Sentence_Tokenizer()

def test_Remove_Add_Line_Char():
    rm_rule = Remove_Add_Line_Char()
    rm_rule.output = 'rm_out.txt'
    filename = 'rm_char_input.txt'
    rm_rule.run([filename])
    with codecs.open(rm_rule.output,'r','utf-8') as f:
        lines = f.readlines()
    assert len(lines) == 14
    with codecs.open(filename,'r','utf-8') as f1:
        lines = f1.readlines()
        assert len(lines) == 17
test_Remove_Add_Line_Char()

class bifrost_simulate:
    def post_process(self, line):
        return line.replace("CENTEr", "中间")

    def pre_process(self, line):
        return line.replace("good", "nice")

def test_Align_Target_Source():
    post_schema_path = '../schema_law_zh2en_post_context.json'
    bifrost_instance = bifrost_simulate()
    post_rule_engine = rule_engine.RuleEngine(
        post_schema_path,
        None,
        mode='lib',
        rule_engine_context={'bifrost': bifrost_instance})
    context = {"tgt_array": ["The", "refrac@@", "tory", "clay", "is", "soil", "and", "its", "aluminum", "is", "less", "than", "2", "", "6", ",", "and", "the", "aluminum", "content", "is", "more", "than", "30", "%", "."], "align_enabled": True, "raw_line": "耐@@ 火 粘@@ 土 呈 土@@ 状 , 其 铝 硅 比 小于 2  6 , 含@@ 铝@@ 量 一般 大于 30 % 。", "src_array": ["耐@@", "火", "粘@@", "土", "呈", "土@@", "状", ",", "其", "铝", "硅", "比", "小于", "2", "", "6", ",", "含@@", "铝@@", "量", "一般", "大于", "30", "%", "。"], "line": "The refrac@@ tory clay is soil and its aluminum is less than 2  6 , and the aluminum content is more than 30 % .", "tgt_src_mapping": [1, 1, 1, 2, 4, 5, 6, 9, 9, 10, 12, 13, 13, 14, 15, 16, 18, 18, 18, 17, 17, 20, 21, 22, 23, 20]}
    post_rule_engine.execute(context,True)
    res = []
    for i, index in enumerate(context['mapping']):
        res.append(' '.join([context['target'][i], context['source'][index]]))
    assert '\n'.join(res) == '''The refractory 耐火
clay 粘土
is 呈
soil and 土状
its aluminum 铝
is 硅
less 小于
than 2 2
 
6 6
, ,
and the aluminum content is 含铝量
more 一般
than 大于
30 30
% %
. 一般'''
    context = {"tgt_array": ["When", "the", "local", "<->","people", "&apos;s", "congresses", "at", "or", "above", "the", "county", "level", "hold", "a", "meeting", ",", "the", "deputies", "who", "have", "been", "proposed", "to", "be", "removed", "shall", "have", "the", "right", "to", "submit", "their", "arguments", "in", "the", "meeting", "of", "the", "presidium", "and", "the", "plenary", "meeting", "of", "the", "General", "Assembly", ",", "or", "make", "a", "written", "defense", "in", "writing", ",", "and", "the", "presidium", "shall", "issue", "the", "meeting", "."], "align_enabled": True, "raw_line": "县级 以上 的 地方 各级 人民代表大会 举行 会议 的 时候 , 被 提出 罢免 的 代表 有权 在 主席团 会议 和 大会 全体会议 上 提出 申@@ 辩 意见 , 或者 书面 提出 申@@ 辩 意见 , 由 主席团 印发 会议 。", "src_array": ["县级", "以上", "的", "地方", "各级", "人民代表大会", "举行", "会议", "的", "时候", ",", "被", "提出", "罢免", "的", "代表", "有权", "在", "主席团", "会议", "和", "大会", "全体会议", "上", "提出", "申@@", "辩", "意见", ",", "或者", "书面", "提出", "申@@", "辩", "意见", ",", "由", "主席团", "印发", "会议", "。"], "line": "When the local people &apos;s congresses at or above the county level hold a meeting , the deputies who have been proposed to be removed shall have the right to submit their arguments in the meeting of the presidium and the plenary meeting of the General Assembly , or make a written defense in writing , and the presidium shall issue the meeting .", "tgt_src_mapping": \
        [9, 6, 5, 5,5, 5, 5, 4, 1, 1, 0, 0, 0, 7, 7, 7, 10, 15, 15, 12, 12, 12, 13, 13, 13, 13, 16, 16, 16, 16, 17, 26, 26, 26, 28, 18, 18, 20, 18, 18, 20, 21, 22, 22, 29, 21, 21, 21, 29, 29, 31, 33, 33, 33, 34, 30, 36, 36, 38, 37, 38, 38, 39, 39, 40]}
    post_rule_engine.execute(context,True)
    res1 = []
    for i, index in enumerate(context['mapping']):
        res1.append(' '.join([context['target'][i], context['source'][index]]))
    assert '\n'.join(res1) == '''When 时候
the 举行
local-people's congresses 人民代表大会
at 各级
or above 以上
the county level 县级
hold a meeting 会议
, ,
the deputies 代表
who have been 提出
proposed to be removed 罢免
shall have the right 有权
to 在
submit their arguments 申辩
in ,
the meeting 主席团
of 和
the presidium 主席团
and 和
the 大会
plenary meeting 全体会议
of 或者
the General Assembly 大会
, or 或者
make 提出
a written defense 申辩
in 意见
writing 书面
, and 由
the 印发
presidium 主席团
shall issue 印发
the meeting 会议
. 。'''
test_Align_Target_Source()

test_data_restore_word_case =[
    {
        "raw_line":u"Including the above-mentioned ADRs, the following table lists the ADRs reported with the use of Sibelium in the context of clinical trials and post-marketing experience.",
        "line":u"包括上述adr，下表列出了在临床试验和上市后经验中使用Sibelium报告的adr。 "
    },
    {
        "raw_line":u"These risk factors will include: abnormal free light chain (FLC) ratio (<0.126 or >8), serum M-protein ≥3 g/dL, urine M-protein >500mg/24 hours, IgA subtype, and immunoparesis (at least 1 uninvolved immunoglobulin [IgG, IgA, IgM] decreased more than 25% below lower limit of normal [LLN]).",
        "line":u"这些风险因素将包括：异常游离轻链（flc）比率（<0.126或>8），血清M蛋白≥3 g/dL，尿M蛋白>500 mg/24小时，IgA亚型和免疫缺陷（至少1个未参与的免疫球蛋白[IgG，IgA，IgM]低于正常[lln]）。"
    },
    {
        "raw_line":u"All summaries of AEs will be based on treatment-emergent adverse events  (TEAEs) , defined as any AE that occurs after the first administration of study agent through 30 days after the last study agent administration; or any AE that is considered drug-related  (very likely, probably, or possibly related)  regardless of the start date of the event; or any AE that is present at baseline but worsens in toxicity grade or is subsequently considered drug-related by the investigator.",
        "line":u"所有ae的摘要将基于治疗紧急不良事件 （teae） 定义为在最后一次研究药物给药后30天首次施用研究药物后发生的任何AE;或任何被认为与药物相关的AE （很可能，可能或可能相关） 不管事件的开始日期;或在基线时存在但在毒性等级中恶化或随后被研究者认为与药物相关的任何AE。"
    },
    {
        "raw_line":u"Incidence of most common (at least 10% in any arm) TEAEs by MedDRA SOC and preferred term",
        "line":u"MedDRA SOC和优选术语最常见的（任何手臂中至少10％）teae的发生率"
    },
    {
        "raw_line":u"Incidence of toxicity grade 3 or 4 TEAEs considered by the investigator to be reasonably related to study agent, by MedDRA SOC and preferred term TEAEs.",
        "line":u"研究者认为与研究药物合理相关的teae的发生率，MedDRA SOC和首选术语teae."
    }
]


def test_word_case():
    rule_engine_context = {}
    rule_engine_context["bifrost"] = bifrost_simulate()
    expect_res ='''包括上述ADR，下表列出了在临床试验和上市后经验中使用Sibelium报告的ADR。
这些风险因素将包括：异常游离轻链（FLC）比率（<0.126或>8），血清M蛋白≥3 g/dL，尿M蛋白>500 mg/24小时，IgA亚型和免疫缺陷（至少1个未参与的免疫球蛋白[IgG，IgA，IgM]低于正常[LLN]）。
所有AE的摘要将基于治疗紧急不良事件（TEAE）定义为在最后一次研究药物给药后30天首次施用研究药物后发生的任何AE;或任何被认为与药物相关的AE（很可能，可能或可能相关）不管事件的开始日期;或在基线时存在但在毒性等级中恶化或随后被研究者认为与药物相关的任何AE。
MedDRA SOC和优选术语最常见的（任何手臂中至少10％）TEAE的发生率
研究者认为与研究药物合理相关的TEAE的发生率，MedDRA SOC和首选术语TEAE.'''
    ruleEngine = rule_engine.RuleEngine(
        "../schema_lib_tech_zh_post_gpu_context.json",
        None,
        mode='lib',
        rule_engine_context=rule_engine_context)
    restored_sen = []
    for data in test_data_restore_word_case:
        print "before restore word case:"
        print data['line']
        ruleEngine.execute(data, True)
        print "after restore word case:"
        print data['line']
        restored_sen.append(data['line'])
    assert '\n'.join(restored_sen) == expect_res
test_word_case()
from rule_common import General_Sentence_Detokenizer_Bracketfix
def test_bracket_and_slash_space():
    post_proc = General_Sentence_Detokenizer_Bracketfix()
    bracket_data = '( No. { 445 &#91; 2012 &#93; of the State Administration of Taxation)'
    slash_data = "1. For an ordinary resolution, there shall be the shareholders holding 1 / 2 or more of the total shares attending the shareholders' \\ meeting,"
    fix_data = 'The Working Rules of the Review Committee for the Reorganization of Listed Companies of the China Securities Regulatory Commission ( No. 41 &#91; 2004 &#93; , CSRC ) issued on May 12 , 2004 shall be repealed simultaneously .'
    test_bracket1=' ( No. 132 &#91; 2004 &#93; of the State Administration of Taxation )'
    test_bracket2='7 . Notice on the inability of banks and credit cooperatives to handle the insurance business ( No. 136 &#91; 1987 &#93; of the People &apos;s Bank of China )'
    assert post_proc.run(slash_data) == '''1. For an ordinary resolution, there shall be the shareholders holding 1/2 or more of the total shares attending the shareholders'\meeting,'''
    assert post_proc.run(bracket_data) == '''(No. {445 [2012] of the State Administration of Taxation)'''
    assert post_proc.run(fix_data) == '''The Working Rules of the Review Committee for the Reorganization of Listed Companies of the China Securities Regulatory Commission (No. 41 [2004], CSRC) issued on May 12, 2004 shall be repealed simultaneously.'''
    assert post_proc.run(test_bracket1) == '''(No. 132 [2004] of the State Administration of Taxation)'''
    assert post_proc.run(test_bracket2) == '''7. Notice on the inability of banks and credit cooperatives to handle the insurance business (No. 136 [1987] of the People's Bank of China)'''
test_bracket_and_slash_space()

def verify_post_context_rule():
    context = {}
    context["line"] = "i start 中文 很好 i center 晚餐 end i [pet-dn] ' abc & def _ g : ood & bad' 翻译 i"
    context["raw_line"] = "I STarT Chinese good I CENTEr dinner END I [PET-DN] 'ABc&DEF_G:Ood&bAd' translate I"
    rule_engine_context = {}
    rule_engine_context["bifrost"] = bifrost_simulate()

    ruleEngine = rule_engine.RuleEngine(
        "../schema_lib_tech_zh_post_gpu_context.json",
        None,
        mode='lib',
        rule_engine_context=rule_engine_context)

    ruleEngine.execute(context, True)

    print context["line"]
    assert context["line"] == "I STarT中文很好I中间晚餐END I[PET-DN]'ABc&DEF_G:Ood&bAd'翻译I"

    # regression test for infinite loop.
    print "starting infinite loop test. If the test is not finished in serveral seconds, then something wrong."
    context["line"] = "在 pet / mr m3 项目 中 ， pet 和 患者 表 子系统 保持 不变 ， 而 mr 子系统 升级 到 具有 多 传输 （ tx ） 功能 的 xx@@ x <N> t “ tx ” 。"
    context["raw_line"] = "in the pet / mr m3 project , the pet and patient table sub@@ systems remains unchanged while the mr sub@@ system upgrades to an xx@@ x <N> t &quot; tx &quot; with the multi <-> transmit ( tx ) functionality ."
    ruleEngine.execute(context, True)
    print "finished infinite loop test."

def verify_pre_context_rule():
    context = {}
    context["line"] = "STarT Chinese good CENTEr dinner END"
    rule_engine_context = {}
    rule_engine_context["bifrost"] = bifrost_simulate()

    ruleEngine = rule_engine.RuleEngine(
        "../schema_lib_tech_en_pre_gpu_context.json",
        None,
        mode='lib',
        rule_engine_context=rule_engine_context)

    ruleEngine.execute(context, True)
    assert context["line"] == "start chinese nice center dinner end"


def verify_pre_context_rule_with_real_bifrost():
    context = {}
    context["line"] = "STarT Chinese good CENTEr dinner END"
    rule_engine_context = {}
    rule_engine_context["bifrost"] = Bifrost('../data/rule.txt')

    ruleEngine = rule_engine.RuleEngine(
        "../schema_lib_tech_en_pre_gpu_context.json",
        None,
        mode='lib',
        rule_engine_context=rule_engine_context)

    ruleEngine.execute(context, True)
    print context["line"]
    assert context["line"] == "start chinese good center dinner end"


def verify_pre_context_rule_with_bpe():
    context = {}
    context["line"] = "Proteinuria is defined as more than 3000 mg in a 24-hour collection. whichone?"
    rule_engine_context = {}
    rule_engine_context["bifrost"] = Bifrost('../data/rule.txt')
    rule_engine_context["bpe"] = BPE(file('../data/codebook.en.txt'), '@@', file('../data/nonbreakword.en.txt'))

    ruleEngine = rule_engine.RuleEngine(
        "../schema_lib_medical_en_pre_gpu_context.json",
        None,
        mode='lib',
        rule_engine_context=rule_engine_context)

    ruleEngine.execute(context, True)
    print context["line"]
    assert context["line"] == "proteinuria is defined as more than <N:MzAwMA==> mg in a 24 <-> hour collec@@ tion. which@@ one ?"


verify_post_context_rule()
verify_pre_context_rule()
verify_pre_context_rule_with_real_bifrost()
verify_pre_context_rule_with_bpe()
