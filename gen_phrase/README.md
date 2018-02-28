File listing:
----------------------------
- anymalign.py: anymalign算法
- filter.py: 自定义过滤脚本
- filter_conf.json: 过滤规则配置文件
- run_align.sh: 启动脚本
- options: anymalign算法参数说明
- README.md


Description
----------------------------
本程序的目标是以平行语料作为输入，输出高质量的平行短语对。包括两个阶段：抽取和过滤，通过run_align.sh来控制运行的流程。抽取阶段由anymalign.py来执行，如果run_align.sh中的run_anymalign变量设置为1，则启动抽取过程；可以根据需求，对anymalign的执行参数进行设定，包括短语的长度范围，采样时长和一次性加载的句对数量（语料较大，无法完全load的情况）等，详情见options文件。filter.py负责过滤操作，由run_align.sh中的run_filter变量控制是否启动；可以在filter_conf.json中配置过滤规则，每条rule在filter.py中有对应的执行逻辑，由judge函数循环调用。若新增过滤规则，需在filter_conf.json中添加规则名和参数，然后在filter.py中实现过滤逻辑。

File format
----------------------------
##### 1. 平行语料
分离的文本文件，对应的行互为翻译

源文件
```
He is one of my friends.
She put a bunch of flowers by the edge of the table.
```
目标文件
```
他是我的朋友。
她把一束花放在桌边。
```

##### 2. 短语对齐文件
每行是一对短语，包括5个字段：源短语，目标短语，词汇权重，翻译概率和频率，以 \t 分隔
```
a bunch of flowers \t 一束花 \t 0.98 0.86 \t 1.0 0.5 \t 1276
```
其中词汇权重和翻译概率均包含源到目标和目标到源的两个值，以空格分隔


Rules
----------------------------
```
multi_align：          一对多对齐，选择翻译概率大于0.5的即可，既可以保证是概率最大的翻译，同时可信度高；
en_no_en：             英文短语中不包含字母；
zh_no_zh：             中文短语中不包含中文字；
en_has_zhPunc：        英文短语中有中文标点；
zh_has_enPunc：        中文短语中有英文标点；
start_with_Punc：      短语的开始字符是标点；
zh_start_with_special：中文短语以特殊词开始，比如‘了’和‘的’；
en_end_with_special：  英文短语以特殊单词结束，比如'the'；
en_paren_mismatch：    英文短语中括号不匹配；
zh_paren_mismatch：    中文短语中括号不匹配；
ptr_sum_low：          双向翻译概率的和小于阈值；
ptr_or_low：           存在一个方向的翻译概率小于阈值；
lexicalW_zero：        至少存在一个方向的lexical权重等于0，虽然lexical权重波动较大，不过等于0的情况下大多数存在对齐偏差；
len_diff：             中英文短语的长度比超出阈值，把长度差限定在合理的区间；
```
备注：根据需求，可以变更括号匹配的类型；和标点相关的rule，都可以配置对应的标点符号集；翻译概率的阈值调大，过滤会更严格，短语对的精度会提高，但是获取的短语数量会减少，可根据需求进行权衡。


Usage
----------------------------
##### Requirements
- numpy
- json

```
$ git clone https://github.com/AtmanCorp/data-process.git
$ cd data-process/data_process/gen_phrase/
$ ./run_align.sh <source> <target>

```


Contact
----------------------------
* 张明华
* zhangmh1993@163.com
* Atman Corp

