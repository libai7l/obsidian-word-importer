#!/usr/bin/env python3
"""
Obsidian Word Importer v2.1 - Native Messaging Host
CET-6 + 通用科研词汇 | 音标发音 | 词根词缀分析 | 词组支持 | 按字母排序
"""
import sys, json, struct, os, re, urllib.request, urllib.error
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════
# CET-6 + 测绘专业 + 学术词汇 综合词库 (音标/词性/释义/词根词缀)
# 格式: word: (pronunciation, pos, meaning, etymology_hint)
# ══════════════════════════════════════════════════════════════════════

FULL_DICT = {
    # ────────── CET-6 高频核心词 (300+) ──────────
    "abandon": ("/əˈbændən/", "v.", "放弃；抛弃", "a-(不)+ban(禁止)+don(给予)→放弃"),
    "abnormal": ("/æbˈnɔːrml/", "adj.", "不正常的", "ab-(偏离)+normal(正常的)"),
    "abolish": ("/əˈbɒlɪʃ/", "v.", "废除；取消", "ab-(离开)+ol(生长)+ish→废除"),
    "abrupt": ("/əˈbrʌpt/", "adj.", "突然的；唐突的", "ab-(离开)+rupt(断裂)→突然断裂"),
    "absorb": ("/əbˈzɔːrb/", "v.", "吸收；吸引", "ab-(离开)+sorb(吸)→吸走"),
    "abstract": ("/ˈæbstrækt/", "adj./n.", "抽象的；摘要", "abs-(离开)+tract(拉)→拉开→抽象"),
    "abundant": ("/əˈbʌndənt/", "adj.", "丰富的；充裕的", "ab-(加强)+und(波浪)+ant→多如波浪"),
    "abuse": ("/əˈbjuːz/", "v./n.", "滥用；虐待", "ab-(偏离)+use(使用)→滥用"),
    "academic": ("/ˌækəˈdemɪk/", "adj.", "学术的；学院的", "academ(学院)+ic"),
    "accelerate": ("/əkˈseləreɪt/", "v.", "加速；促进", "ac-(加强)+celer(快速)+ate→加速"),
    "accessible": ("/əkˈsesəbl/", "adj.", "可接近的；易理解的", "access(进入)+ible(可…的)"),
    "accommodate": ("/əˈkɒmədeɪt/", "v.", "容纳；适应；提供住宿", "ac+com(共同)+mod(方式)+ate→使适应"),
    "accompany": ("/əˈkʌmpəni/", "v.", "陪伴；伴随", "ac-(加强)+company(同伴)→陪伴"),
    "accomplish": ("/əˈkʌmplɪʃ/", "v.", "完成；实现", "ac-(加强)+com(完全)+pl(填满)+ish→完成"),
    "accurate": ("/ˈækjərət/", "adj.", "准确的；精确的", "ac-(加强)+cur(关心)+ate→仔细→准确"),
    "accuse": ("/əˈkjuːz/", "v.", "指控；指责", "ac-(朝向)+cuse(原因)→归咎于"),
    "achieve": ("/əˈtʃiːv/", "v.", "达到；取得", "a-(到)+chieve(头)→到头→完成"),
    "acknowledge": ("/əkˈnɒlɪdʒ/", "v.", "承认；确认；感谢", "ac+knowledge(知识)→承认知道"),
    "acquire": ("/əˈkwaɪər/", "v.", "获得；习得", "ac-(加强)+quire(寻求)→获得"),
    "adapt": ("/əˈdæpt/", "v.", "适应；改编", "ad-(朝向)+apt(适合)→使适合"),
    "adequate": ("/ˈædɪkwət/", "adj.", "足够的；适当的", "ad-(到)+equ(相等)+ate→与需求相等→足够的"),
    "adjust": ("/əˈdʒʌst/", "v.", "调整；适应", "ad-(朝向)+just(正确)→使正确→调整"),
    "administration": ("/ədˌmɪnɪˈstreɪʃn/", "n.", "管理；行政", "ad+ministr(服务)+ation→管理"),
    "adolescent": ("/ˌædəˈlesnt/", "n./adj.", "青少年；青春期的", "adol(成年)+escent(开始)→开始成年"),
    "adverse": ("/ˈædvɜːrs/", "adj.", "不利的；相反的", "ad-(朝向)+verse(转)→转向→对立"),
    "advocate": ("/ˈædvəkeɪt/", "v./n.", "提倡；倡导者", "ad-(加强)+voc(呼喊)+ate→大声呼吁"),
    "aesthetic": ("/iːsˈθetɪk/", "adj.", "美学的；审美的", "aesthet(感觉)+ic→感觉美"),
    "affection": ("/əˈfekʃn/", "n.", "喜爱；感情", "af-(加强)+fect(做)+ion→做出感情"),
    "aggressive": ("/əˈɡresɪv/", "adj.", "侵略的；好斗的", "ag-(加强)+gress(走)+ive→向前走→侵略"),
    "allocate": ("/ˈæləkeɪt/", "v.", "分配；拨出", "al-(到)+loc(位置)+ate→放到位置→分配"),
    "alternative": ("/ɔːlˈtɜːrnətɪv/", "n./adj.", "替代方案；替代的", "altern(交替)+ative→交替的"),
    "ambiguous": ("/æmˈbɪɡjuəs/", "adj.", "模糊的；歧义的", "ambi-(两边)+gu(驱动)+ous→两边驱动→模糊"),
    "ambitious": ("/æmˈbɪʃəs/", "adj.", "有雄心的", "ambi-(周围)+it(走)+ious→四处奔走→有雄心"),
    "analogy": ("/əˈnælədʒi/", "n.", "类比；相似", "ana-(按)+log(说)+y→按比例说→类比"),
    "anchor": ("/ˈæŋkər/", "n./v.", "锚；固定；主持", "anch(弯曲)+or→弯曲的钩子→锚"),
    "anonymous": ("/əˈnɒnɪməs/", "adj.", "匿名的", "an-(无)+onym(名字)+ous→无名的"),
    "apparatus": ("/ˌæpəˈreɪtəs/", "n.", "仪器；设备", "ap-(加强)+par(准备)+atus→准备好的东西"),
    "apparent": ("/əˈpærənt/", "adj.", "明显的；表面的", "ap-(加强)+par(出现)+ent→显现的"),
    "appetite": ("/ˈæpɪtaɪt/", "n.", "食欲；欲望", "ap-(加强)+pet(追求)+ite→追求→欲望"),
    "appliance": ("/əˈplaɪəns/", "n.", "电器；器械", "apply(应用)+ance(物)→应用的器具"),
    "appreciate": ("/əˈpriːʃieɪt/", "v.", "欣赏；感激；升值", "ap-(加强)+preci(价值)+ate→给予价值"),
    "approach": ("/əˈprəʊtʃ/", "v./n.", "接近；方法", "ap-(到)+proach(近)→接近"),
    "appropriate": ("/əˈprəʊpriət/", "adj.", "适当的；合适的", "ap+propri(自己的)+ate→属于自己的→合适的"),
    "approximate": ("/əˈprɒksɪmət/", "adj./v.", "近似的；接近", "ap+proxim(最近)+ate→近似"),
    "arbitrary": ("/ˈɑːrbɪtreri/", "adj.", "任意的；武断的", "arbitr(仲裁者)+ary→仲裁者自行决定"),
    "artificial": ("/ˌɑːrtɪˈfɪʃl/", "adj.", "人工的；人造的", "art(艺术)+fic(做)+ial→人工做的"),
    "assemble": ("/əˈsembl/", "v.", "组装；集合", "as-(到)+semble(一起)→到一起→集合"),
    "assert": ("/əˈsɜːrt/", "v.", "断言；坚持主张", "as-(加强)+sert(连接)→坚定连接→断言"),
    "assess": ("/əˈses/", "v.", "评估；评定", "as-(旁)+sess(坐)→坐在旁边评判→评估"),
    "assign": ("/əˈsaɪn/", "v.", "分配；指派", "as-(到)+sign(标记)→标记到→分配"),
    "associate": ("/əˈsəʊʃieɪt/", "v.", "联系；关联", "as+soci(同伴)+ate→成为同伴→联系"),
    "assume": ("/əˈsjuːm/", "v.", "假设；承担", "as-(加强)+sume(拿取)→拿取→假设"),
    "atmosphere": ("/ˈætməsfɪr/", "n.", "大气；氛围", "atmo(蒸汽)+sphere(球体)→大气层"),
    "attach": ("/əˈtætʃ/", "v.", "附加；依恋", "at-(到)+tach(接触)→接触到→附加"),
    "attain": ("/əˈteɪn/", "v.", "达到；获得", "at-(到)+tain(触碰)→触碰到→达到"),
    "attribute": ("/əˈtrɪbjuːt/", "v./n.", "归因于；属性", "at+tribute(给予)→给予→归因"),
    "authentic": ("/ɔːˈθentɪk/", "adj.", "真实的；可靠的", "authent(作者本人)+ic→原作→真实"),
    "authority": ("/əˈθɒrəti/", "n.", "权威；当局", "author(作者)+ity→作者有权威"),
    "automatic": ("/ˌɔːtəˈmætɪk/", "adj.", "自动的", "auto-(自己)+mat(动)+ic→自动的"),
    "autonomous": ("/ɔːˈtɒnəməs/", "adj.", "自治的；自主的", "auto-(自己)+nom(法则)+ous→自主的"),
    "available": ("/əˈveɪləbl/", "adj.", "可用的；有效的", "avail(有用)+able(可…的)→可用的"),
    "awkward": ("/ˈɔːkwərd/", "adj.", "尴尬的；笨拙的", "awk(错误方向)+ward(朝向)→朝向错误→尴尬"),
    "barrier": ("/ˈbæriər/", "n.", "障碍；屏障", "barr(棒)+ier→木棒→障碍"),
    "beneath": ("/bɪˈniːθ/", "prep.", "在…之下", "be-(在)+neath(下方)→在下方"),
    "beneficial": ("/ˌbenɪˈfɪʃl/", "adj.", "有益的", "bene-(好)+fic(做)+ial→做好事→有益的"),
    "boundary": ("/ˈbaʊndri/", "n.", "边界；界限", "bound(界限)+ary(场所)→边界"),
    "budget": ("/ˈbʌdʒɪt/", "n./v.", "预算；编预算", "budg(皮包)+et(小)→小皮包→钱袋→预算"),
    "burden": ("/ˈbɜːrdn/", "n./v.", "负担；使负重", "burd(承担)+en→负担"),
    "calculate": ("/ˈkælkjuleɪt/", "v.", "计算；估计", "calc(石头)+ul(小)+ate→用小石子计数→计算"),
    "campaign": ("/kæmˈpeɪn/", "n./v.", "运动；战役", "camp(田野)+aign→在田野上→战役"),
    "capable": ("/ˈkeɪpəbl/", "adj.",  "有能力的", "cap(拿)+able(能)→能拿住的→有能力的"),
    "capacity": ("/kəˈpæsəti/", "n.", "容量；能力", "cap(拿)+acity→拿住的能力→容量"),
    "capture": ("/ˈkæptʃər/", "v./n.", "捕获；俘获", "capt(抓取)+ure→捕获"),
    "catalogue": ("/ˈkætəlɒɡ/", "n./v.", "目录；编目", "cata-(完全)+logue(说)→完整说明→目录"),
    "category": ("/ˈkætəɡɔːri/", "n.", "类别；范畴", "cate-(完全)+gor(集会)+y→完全分类"),
    "cautious": ("/ˈkɔːʃəs/", "adj.", "谨慎的", "caut(小心)+ious→小心的"),
    "cease": ("/siːs/", "v./n.", "停止；终止", "cease(退让)→停止"),
    "challenge": ("/ˈtʃælɪndʒ/", "n./v.", "挑战；质疑", "chall(虚假指控)+enge→挑战"),
    "characteristic": ("/ˌkærəktəˈrɪstɪk/", "n./adj.", "特征；特有的", "character(特征)+istic→特征"),
    "circumstance": ("/ˈsɜːrkəmstæns/", "n.", "环境；情况", "circum-(周围)+stance(站立)→周围站立→环境"),
    "civilization": ("/ˌsɪvələˈzeɪʃn/", "n.", "文明；文化", "civil(公民的)+ization→文明"),
    "clarify": ("/ˈklærɪfaɪ/", "v.", "澄清；阐明", "clar(清楚)+ify(使)→使清楚"),
    "classify": ("/ˈklæsɪfaɪ/", "v.", "分类；归类", "class(类别)+ify(使)→分类"),
    "client": ("/ˈklaɪənt/", "n.", "客户；委托人", "cli(倚靠)+ent→倚靠者→委托人"),
    "cognitive": ("/ˈkɒɡnɪtɪv/", "adj.", "认知的", "cogn(知道)+itive→认知的"),
    "coincidence": ("/kəʊˈɪnsɪdəns/", "n.", "巧合；一致", "co-(共同)+incidence(发生)→同时发生→巧合"),
    "collapse": ("/kəˈlæps/", "v./n.", "倒塌；崩溃", "col-(一起)+lapse(滑倒)→一起滑倒→坍塌"),
    "colleague": ("/ˈkɒliːɡ/", "n.", "同事", "col-(共同)+league(联盟)→共同联盟→同事"),
    "commentary": ("/ˈkɒmənteri/", "n.", "评论；解说", "comment(评论)+ary→评论"),
    "commit": ("/kəˈmɪt/", "v.", "犯(罪)；委托；承诺", "com-(加强)+mit(发送)→发送→委托"),
    "commodity": ("/kəˈmɒdəti/", "n.", "商品；日用品", "com+mod(方式)+ity→各种方式→商品"),
    "communicate": ("/kəˈmjuːnɪkeɪt/", "v.", "交流；传达", "com+mun(公共)+icate→使公共→交流"),
    "community": ("/kəˈmjuːnəti/", "n.", "社区；群体", "com+mun(公共)+ity→公共群体"),
    "comparable": ("/ˈkɒmpərəbl/", "adj.", "可比较的；类似的", "compar(比较)+able→可比较的"),
    "compatible": ("/kəmˈpætəbl/", "adj.", "兼容的；和睦的", "com+pat(承受)+ible→共同承受→兼容"),
    "compensate": ("/ˈkɒmpenseɪt/", "v.", "补偿；赔偿", "com+pens(称量)+ate→一起称量→补偿"),
    "competent": ("/ˈkɒmpɪtənt/", "adj.", "有能力的；胜任的", "com+pet(追求)+ent→共同追求→胜任"),
    "compile": ("/kəmˈpaɪl/", "v.", "编译；汇编", "com-(一起)+pile(堆)→堆在一起→汇编"),
    "complement": ("/ˈkɒmplɪment/", "v./n.", "补充；补足", "com+ple(填满)+ment→补充"),
    "complex": ("/ˈkɒmpleks/", "adj./n.", "复杂的；复合体", "com+plex(折叠)→折叠在一起→复杂"),
    "complicate": ("/ˈkɒmplɪkeɪt/", "v.", "使复杂化", "com+plic(折叠)+ate→折叠→复杂"),
    "component": ("/kəmˈpəʊnənt/", "n./adj.", "组件；组成的", "com+pon(放置)+ent→放在一起→组件"),
    "compose": ("/kəmˈpəʊz/", "v.", "组成；创作", "com+pose(放置)→放在一起→组成"),
    "comprehend": ("/ˌkɒmprɪˈhend/", "v.", "理解；包含", "com+prehend(抓住)→全部抓住→理解"),
    "comprehensive": ("/ˌkɒmprɪˈhensɪv/", "adj.", "全面的；综合的", "com+prehens(抓住)+ive→全部抓住"),
    "comprise": ("/kəmˈpraɪz/", "v.", "包含；由…组成", "com+prise(抓住)→抓在一起→包含"),
    "compromise": ("/ˈkɒmprəmaɪz/", "n./v.", "妥协；折中", "com+promise(承诺)→共同承诺→妥协"),
    "concentrate": ("/ˈkɒnsntreɪt/", "v.", "集中；专注", "con+centr(中心)+ate→到中心→集中"),
    "concept": ("/ˈkɒnsept/", "n.", "概念；观念", "con+cept(拿取)→拿取→形成概念"),
    "concrete": ("/ˈkɒŋkriːt/", "adj./n.", "具体的；混凝土", "con+crete(生长)→长在一起→具体的"),
    "conference": ("/ˈkɒnfərəns/", "n.", "会议；讨论", "con+fer(带来)+ence→带到一起→会议"),
    "confident": ("/ˈkɒnfɪdənt/", "adj.", "自信的；确信的", "con+fid(信任)+ent→完全信任→自信"),
    "confine": ("/kənˈfaɪn/", "v.", "限制；禁闭", "con+fine(边界)→在边界内→限制"),
    "confirm": ("/kənˈfɜːrm/", "v.", "确认；证实", "con+firm(坚定)→使坚定→确认"),
    "conflict": ("/ˈkɒnflɪkt/", "n./v.", "冲突；矛盾", "con+flict(打击)→互相打击→冲突"),
    "confront": ("/kənˈfrʌnt/", "v.", "面对；对抗", "con+front(前面)→面对面→对抗"),
    "conscience": ("/ˈkɒnʃəns/", "n.", "良心；良知", "con+science(知识)→良知"),
    "conscious": ("/ˈkɒnʃəs/", "adj.", "有意识的；清醒的", "con+sci(知道)+ous→知道的→有意识"),
    "consensus": ("/kənˈsensəs/", "n.", "共识；一致意见", "con+sensus(感觉)→共同感觉→共识"),
    "consequence": ("/ˈkɒnsɪkwəns/", "n.", "结果；后果", "con+sequ(跟随)+ence→跟随而来→后果"),
    "conservative": ("/kənˈsɜːrvətɪv/", "adj.", "保守的", "con+serv(保持)+ative→保持原样→保守"),
    "considerable": ("/kənˈsɪdərəbl/", "adj.", "相当大的", "consider(考虑)+able→值得考虑的→相当大的"),
    "consistent": ("/kənˈsɪstənt/", "adj.", "一致的；始终如一的", "con+sist(站立)+ent→站在一起→一致"),
    "constant": ("/ˈkɒnstənt/", "adj.", "不变的；恒定的", "con+stant(站立)→一直站着→恒定"),
    "constitute": ("/ˈkɒnstɪtjuːt/", "v.", "构成；建立", "con+stitute(建立)→建立→构成"),
    "constrain": ("/kənˈstreɪn/", "v.", "约束；限制", "con+strain(拉紧)→拉紧→约束"),
    "construct": ("/kənˈstrʌkt/", "v.", "建设；构建", "con+struct(建造)→建造→构建"),
    "consult": ("/kənˈsʌlt/", "v.", "咨询；查阅", "con+sult(召集)→召集商议→咨询"),
    "consume": ("/kənˈsjuːm/", "v.", "消费；消耗", "con+sume(拿取)→全部拿走→消耗"),
    "contact": ("/ˈkɒntækt/", "n./v.", "接触；联系", "con+tact(触碰)→互相触碰→联系"),
    "contemporary": ("/kənˈtempəreri/", "adj.", "当代的；同时代的", "con+tempor(时间)+ary→同时代"),
    "contradict": ("/ˌkɒntrəˈdɪkt/", "v.", "矛盾；反驳", "contra-(反)+dict(说)→反着说→反驳"),
    "contribute": ("/kənˈtrɪbjuːt/", "v.", "贡献；捐助", "con+tribute(给予)→给予→贡献"),
    "controversial": ("/ˌkɒntrəˈvɜːrʃl/", "adj.", "有争议的", "contro(反)+vers(转)+ial→反转→争议"),
    "convenient": ("/kənˈviːniənt/", "adj.", "方便的", "con+ven(来)+ient→来到一起→方便"),
    "conventional": ("/kənˈvenʃənl/", "adj.", "传统的；惯例的", "convention(惯例)+al→传统的"),
    "convert": ("/kənˈvɜːrt/", "v.", "转换；转变", "con+vert(转)→完全转→转换"),
    "convey": ("/kənˈveɪ/", "v.", "传达；运送", "con+vey(路)→上路→运送"),
    "convince": ("/kənˈvɪns/", "v.", "使确信；说服", "con+vince(征服)→征服→说服"),
    "cooperate": ("/kəʊˈɒpəreɪt/", "v.", "合作", "co-(共同)+operate(运作)→合作"),
    "coordinate": ("/kəʊˈɔːrdɪneɪt/", "v./n.", "协调；坐标", "co+ordin(顺序)+ate→按顺序→协调"),
    "correlate": ("/ˈkɒrəleɪt/", "v.", "相关；关联", "cor+relate(关联)→相互关联"),
    "correspond": ("/ˌkɒrəˈspɒnd/", "v.", "对应；通信", "cor+respond(回应)→相互回应→对应"),
    "counsel": ("/ˈkaʊnsl/", "n./v.", "劝告；律师", "coun(一起)+sel(拿)→一起拿主意→劝告"),
    "crisis": ("/ˈkraɪsɪs/", "n.", "危机", "cris(判断)+is→需要判断的时刻→危机"),
    "crucial": ("/ˈkruːʃl/", "adj.", "关键的；决定性的", "cruc(十字)+ial→十字路口→关键"),
    "curiosity": ("/ˌkjʊriˈɒsəti/", "n.", "好奇心", "cur(关心)+iosity→关心→好奇"),
    "debate": ("/dɪˈbeɪt/", "n./v.", "辩论；讨论", "de-(向下)+bate(打)→打下去→辩论"),
    "decline": ("/dɪˈklaɪn/", "v./n.", "下降；拒绝", "de-(向下)+cline(倾斜)→向下倾斜→下降"),
    "dedicate": ("/ˈdedɪkeɪt/", "v.", "奉献；致力于", "de-(完全)+dic(说)+ate→完全说出→奉献"),
    "define": ("/dɪˈfaɪn/", "v.", "定义；界定", "de-(完全)+fine(边界)→划定边界→定义"),
    "demonstrate": ("/ˈdemənstreɪt/", "v.", "展示；证明", "de-(完全)+monstr(显示)+ate→展示"),
    "dense": ("/dens/", "adj.", "浓密的；密集的", "dens(浓厚)+e→浓密"),
    "depict": ("/dɪˈpɪkt/", "v.", "描绘；描述", "de-(加强)+pict(描绘)→描绘"),
    "deposit": ("/dɪˈpɒzɪt/", "v./n.", "存放；存款；沉积", "de+posit(放置)→放下→存放"),
    "derive": ("/dɪˈraɪv/", "v.", "源自；获得", "de-(从)+rive(河流)→从河流来→源自"),
    "desperate": ("/ˈdespərət/", "adj.", "绝望的；不顾一切的", "de-(无)+sper(希望)+ate→无希望"),
    "destination": ("/ˌdestɪˈneɪʃn/", "n.", "目的地；终点", "de-(加强)+stin(站)+ation→目的地"),
    "detect": ("/dɪˈtekt/", "v.", "检测；发现", "de-(除去)+tect(遮盖)→除去遮盖→发现"),
    "deteriorate": ("/dɪˈtɪriəreɪt/", "v.", "恶化；退化", "deterior(更糟)+ate→恶化"),
    "devise": ("/dɪˈvaɪz/", "v.", "设计；发明", "de-(加强)+vise(看)→构思→设计"),
    "dialect": ("/ˈdaɪəlekt/", "n.", "方言", "dia-(之间)+lect(说)→说话的差异→方言"),
    "differentiate": ("/ˌdɪfəˈrenʃieɪt/", "v.", "区分；区别", "different(不同)+iate→区分"),
    "dilemma": ("/dɪˈlemə/", "n.", "困境；两难", "di-(二)+lemma(前提)→两个前提→两难"),
    "dimension": ("/daɪˈmenʃn/", "n.", "维度；尺寸", "di-(加强)+mens(测量)+ion→测量→尺寸"),
    "diminish": ("/dɪˈmɪnɪʃ/", "v.", "减少；缩小", "di-(从)+min(小)+ish→变小→减少"),
    "discard": ("/dɪˈskɑːrd/", "v.", "丢弃；抛弃", "dis-(除去)+card(纸牌)→扔掉牌→丢弃"),
    "discharge": ("/dɪsˈtʃɑːrdʒ/", "v./n.", "排放；解除", "dis-(除去)+charge(装载)→卸下→排放"),
    "discipline": ("/ˈdɪsəplɪn/", "n./v.", "纪律；学科；训练", "discipl(学生)+ine→训练学生→纪律"),
    "discriminate": ("/dɪˈskrɪmɪneɪt/", "v.", "歧视；区分", "dis+crimin(区分)+ate→区分→歧视"),
    "disorder": ("/dɪsˈɔːrdər/", "n.", "混乱；紊乱", "dis-(无)+order(秩序)→无秩序→混乱"),
    "disperse": ("/dɪˈspɜːrs/", "v.", "分散；散开", "di-(分开)+sperse(散开)→分散"),
    "dispose": ("/dɪˈspəʊz/", "v.", "处置；安排", "dis-(分开)+pose(放置)→分开放→处置"),
    "dispute": ("/dɪˈspjuːt/", "n./v.", "争论；争议", "dis-(不同)+pute(思考)→不同想法→争论"),
    "dissolve": ("/dɪˈzɒlv/", "v.", "溶解；解散", "dis-(分开)+solve(解开)→解开→溶解"),
    "distinct": ("/dɪˈstɪŋkt/", "adj.", "明显的；独特的", "di-(分开)+stinct(刺)→刺开→明显"),
    "distinguish": ("/dɪˈstɪŋɡwɪʃ/", "v.", "区分；辨别", "di+stingu(刺)+ish→刺出标记→区分"),
    "distribute": ("/dɪˈstrɪbjuːt/", "v.", "分配；分布", "dis+tribute(给予)→分开给→分配"),
    "diverse": ("/daɪˈvɜːrs/", "adj.", "多样的；不同的", "di-(分开)+verse(转)→转向不同→多样"),
    "domestic": ("/dəˈmestɪk/", "adj.", "国内的；家庭的", "dom(家)+estic→家的→国内的"),
    "dominate": ("/ˈdɒmɪneɪt/", "v.", "主导；支配", "domin(主人)+ate→成为主人→主导"),
    "draft": ("/drɑːft/", "n./v.", "草稿；起草；气流", "draft(拉)→拉出→草稿"),
    "dramatic": ("/drəˈmætɪk/", "adj.", "戏剧性的；巨大的", "drama(戏剧)+tic→戏剧性的"),
    "durable": ("/ˈdjʊərəbl/", "adj.", "耐用的；持久的", "dur(持续)+able→持续的"),
    "elaborate": ("/ɪˈlæbərət/", "adj./v.", "精心的；详细阐述", "e-(出)+labor(劳动)+ate→劳动出来的→精心的"),
    "elegant": ("/ˈelɪɡənt/", "adj.", "优雅的", "e-(出)+leg(选择)+ant→选出来的→优雅"),
    "eliminate": ("/ɪˈlɪmɪneɪt/", "v.", "消除；淘汰", "e-(出)+limin(门槛)+ate→赶出门槛→消除"),
    "embrace": ("/ɪmˈbreɪs/", "v.", "拥抱；包含", "em-(进入)+brace(手臂)→进入手臂→拥抱"),
    "emerge": ("/iˈmɜːrdʒ/", "v.", "出现；浮现", "e-(出)+merge(浸入)→从浸入中出来→浮现"),
    "emphasis": ("/ˈemfəsɪs/", "n.", "强调；重点", "em-(进入)+phas(显示)+is→强调"),
    "empirical": ("/ɪmˈpɪrɪkl/", "adj.", "经验的；实证的", "em+pir(尝试)+ical→尝试的→经验"),
    "encounter": ("/ɪnˈkaʊntər/", "v./n.", "遭遇；遇见", "en+counter(反对)→遭遇反对→遇见"),
    "endeavor": ("/ɪnˈdevər/", "v./n.", "努力；尽力", "en+deavor(义务)→尽义务→努力"),
    "enforce": ("/ɪnˈfɔːrs/", "v.", "执行；强制", "en+force(力量)→用力量→强制"),
    "enormous": ("/ɪˈnɔːrməs/", "adj.", "巨大的", "e-(出)+norm(标准)+ous→超出标准→巨大"),
    "enthusiasm": ("/ɪnˈθjuːziæzəm/", "n.", "热情；热忱", "en+thus(神)+iasm→被神感动→热情"),
    "environment": ("/ɪnˈvaɪrənmənt/", "n.", "环境", "environ(围绕)+ment→围绕物→环境"),
    "episode": ("/ˈepɪsəʊd/", "n.", "插曲；一集", "epi-(旁边)+sode(进入)→旁边插入→插曲"),
    "equivalent": ("/ɪˈkwɪvələnt/", "adj.", "等价的；相等的", "equi(相等)+val(价值)+ent→等价"),
    "essential": ("/ɪˈsenʃl/", "adj.", "本质的；必要的", "ess(存在)+ential→存在的→本质"),
    "establish": ("/ɪˈstæblɪʃ/", "v.", "建立；确立", "e+stabl(稳固)+ish→使稳固→建立"),
    "estate": ("/ɪˈsteɪt/", "n.", "财产；房地产", "e+state(状态)→财产状态→房地产"),
    "estimate": ("/ˈestɪmeɪt/", "v./n.", "估计；估算", "estim(价值)+ate→估算价值"),
    "evaluate": ("/ɪˈvæljueɪt/", "v.", "评估；评价", "e-(出)+valu(价值)+ate→给出价值→评估"),
    "evidence": ("/ˈevɪdəns/", "n.", "证据；迹象", "e-(出)+vid(看)+ence→看出→证据"),
    "evolve": ("/iˈvɒlv/", "v.", "进化；发展", "e-(出)+volve(卷)→卷开→展开→进化"),
    "exaggerate": ("/ɪɡˈzædʒəreɪt/", "v.", "夸张；夸大", "ex+agger(堆)+ate→堆高→夸大"),
    "exceed": ("/ɪkˈsiːd/", "v.", "超过；超越", "ex-(超出)+ceed(走)→走过→超过"),
    "exclusive": ("/ɪkˈskluːsɪv/", "adj.", "独家的；排他的", "ex+clus(关)+ive→关在外面→排他"),
    "execute": ("/ˈeksɪkjuːt/", "v.", "执行；处决", "ex+ecut(跟随)+e→跟随到底→执行"),
    "exert": ("/ɪɡˈzɜːrt/", "v.", "施加；发挥", "ex+ert(连接)→用力连接→施加"),
    "exhibit": ("/ɪɡˈzɪbɪt/", "v./n.", "展览；表现", "ex+hibit(持有)→拿出来→展览"),
    "expedition": ("/ˌekspəˈdɪʃn/", "n.", "远征；探险", "ex+ped(脚)+ition→迈出脚→远征"),
    "explicit": ("/ɪkˈsplɪsɪt/", "adj.", "明确的；显式的", "ex+plic(折叠)+it→展开→明确"),
    "exploit": ("/ɪkˈsplɔɪt/", "v./n.", "利用；开发；剥削", "ex+ploit(折叠)→展开→利用"),
    "extensive": ("/ɪkˈstensɪv/", "adj.", "广泛的；大量的", "ex+tens(延伸)+ive→延伸出去→广泛"),
    "external": ("/ɪkˈstɜːrnl/", "adj.", "外部的", "extern(外部)+al→外部的"),
    "extract": ("/ɪkˈstrækt/", "v./n.", "提取；摘录", "ex+tract(拉)→拉出→提取"),
    "extraordinary": ("/ɪkˈstrɔːrdneri/", "adj.", "非凡的", "extra-(超)+ordinary(普通)→非凡"),
    "facilitate": ("/fəˈsɪlɪteɪt/", "v.", "促进；使便利", "facil(容易)+itate→使容易→促进"),
    "faculty": ("/ˈfæklti/", "n.", "院系；全体教师；能力", "facul(能力)+ty→能力→院系"),
    "feasible": ("/ˈfiːzəbl/", "adj.", "可行的；可能的", "feas(做)+ible(可…的)→可做的→可行"),
    "fluctuate": ("/ˈflʌktʃueɪt/", "v.", "波动；起伏", "fluctu(波浪)+ate→像波浪→波动"),
    "formulate": ("/ˈfɔːrmjuleɪt/", "v.", "制定；公式化", "formul(公式)+ate→公式化"),
    "fundamental": ("/ˌfʌndəˈmentl/", "adj.", "基本的；根本的", "funda(基础)+ment+al→基础的"),
    "generate": ("/ˈdʒenəreɪt/", "v.", "产生；生成", "gener(产生)+ate→产生"),
    "genuine": ("/ˈdʒenjuɪn/", "adj.", "真正的；真诚的", "genu(出生)+ine→天生的→真正"),
    "guarantee": ("/ˌɡærənˈtiː/", "v./n.", "保证；担保", "guar(保护)+antee→保证"),
    "hierarchy": ("/ˈhaɪərɑːrki/", "n.", "层级；等级制度", "hier(神圣)+archy(统治)→等级制度"),
    "highlight": ("/ˈhaɪlaɪt/", "v./n.", "强调；亮点", "high(高)+light(光)→高光→强调"),
    "identical": ("/aɪˈdentɪkl/", "adj.", "完全相同的", "ident(相同)+ical→相同的"),
    "identify": ("/aɪˈdentɪfaɪ/", "v.", "识别；认同", "ident(相同)+ify→识别为相同"),
    "ideology": ("/ˌaɪdiˈɒlədʒi/", "n.", "意识形态", "ideo(观念)+logy(学科)→观念学"),
    "illuminate": ("/ɪˈluːmɪneɪt/", "v.", "照亮；阐明", "il+lumin(光)+ate→照亮"),
    "illustrate": ("/ˈɪləstreɪt/", "v.", "说明；举例说明", "il+lustr(照亮)+ate→照亮→说明"),
    "immense": ("/ɪˈmens/", "adj.", "巨大的；无边的", "im-(无)+mense(测量)→无法测量→巨大"),
    "immigrant": ("/ˈɪmɪɡrənt/", "n.", "移民(迁入)", "im-(进入)+migr(迁移)+ant→迁入者"),
    "implement": ("/ˈɪmplɪment/", "v./n.", "实施；工具", "im+ple(填满)+ment→填满→实施"),
    "implication": ("/ˌɪmplɪˈkeɪʃn/", "n.", "含义；暗示", "im+plic(折叠)+ation→折叠在里面→含义"),
    "impose": ("/ɪmˈpəʊz/", "v.", "强加；施加", "im-(在)+pose(放)→放在上面→强加"),
    "incentive": ("/ɪnˈsentɪv/", "n.", "激励；动机", "in+cent(唱)+ive→唱歌鼓动→激励"),
    "incorporate": ("/ɪnˈkɔːrpəreɪt/", "v.", "合并；纳入", "in+corpor(身体)+ate→成为一体→合并"),
    "indicate": ("/ˈɪndɪkeɪt/", "v.", "指示；表明", "in+dic(说)+ate→说出→指示"),
    "individual": ("/ˌɪndɪˈvɪdʒuəl/", "adj./n.", "个人的；个体", "in+divid(分开)+ual→不可分→个体"),
    "inevitable": ("/ɪnˈevɪtəbl/", "adj.", "不可避免的", "in+evit(避免)+able→不可避"),
    "infrastructure": ("/ˈɪnfrəstrʌktʃər/", "n.", "基础设施", "infra-(下面)+structure(结构)→基础设施"),
    "inherent": ("/ɪnˈhɪərənt/", "adj.", "固有的；内在的", "in+her(黏附)+ent→黏在里面的→固有"),
    "innovation": ("/ˌɪnəˈveɪʃn/", "n.", "创新；革新", "in+nov(新)+ation→创新"),
    "integrate": ("/ˈɪntɪɡreɪt/", "v.", "整合；融合", "integr(完整)+ate→使完整→整合"),
    "intellectual": ("/ˌɪntəˈlektʃuəl/", "adj./n.", "智力的；知识分子", "intel(中间)+lect(选)+ual→从中选出→智力"),
    "intense": ("/ɪnˈtens/", "adj.", "强烈的；紧张的", "in+tens(延伸)→向内延伸→强烈"),
    "interact": ("/ˌɪntərˈækt/", "v.", "互动；相互作用", "inter-(之间)+act(行动)→相互作用"),
    "interfere": ("/ˌɪntərˈfɪr/", "v.", "干涉；干扰", "inter+fer(带来)→带进来→干涉"),
    "intermediate": ("/ˌɪntərˈmiːdiət/", "adj.", "中间的；中级的", "inter+medi(中间)+ate→中间的"),
    "internal": ("/ɪnˈtɜːrnl/", "adj.", "内部的；内在的", "intern(内部)+al→内部的"),
    "interpret": ("/ɪnˈtɜːrprɪt/", "v.", "解释；口译", "inter+pret(表达)→在中间表达→解释"),
    "interval": ("/ˈɪntərvl/", "n.", "间隔；间歇", "inter+val(墙)→墙之间→间隔"),
    "intervene": ("/ˌɪntərˈviːn/", "v.", "干预；介入", "inter+vene(来)→来到中间→介入"),
    "intrinsic": ("/ɪnˈtrɪnsɪk/", "adj.", "内在的；本质的", "intrin(内部)+sic→内在的"),
    "investigate": ("/ɪnˈvestɪɡeɪt/", "v.", "调查；研究", "in+vestig(追踪)+ate→追踪→调查"),
    "involve": ("/ɪnˈvɒlv/", "v.", "涉及；包含", "in+volve(卷)→卷入→涉及"),
    "isolate": ("/ˈaɪsəleɪt/", "v.", "隔离；孤立", "isol(岛)+ate→变成岛→隔离"),
    "justify": ("/ˈdʒʌstɪfaɪ/", "v.", "证明…正当", "just(公正)+ify→使公正→证明"),
    "legislation": ("/ˌledʒɪsˈleɪʃn/", "n.", "立法；法规", "legis(法律)+lat(带来)+ion→立法"),
    "liberal": ("/ˈlɪbərəl/", "adj.", "自由的；开明的", "liber(自由)+al→自由的"),
    "maintain": ("/meɪnˈteɪn/", "v.", "维持；保养", "main(手)+tain(拿住)→用手拿住→维持"),
    "manipulate": ("/məˈnɪpjuleɪt/", "v.", "操纵；控制", "mani(手)+pul(填满)+ate→用手填→操纵"),
    "mechanism": ("/ˈmekənɪzəm/", "n.", "机制；原理", "mechan(机械)+ism→机制"),
    "migrate": ("/maɪˈɡreɪt/", "v.", "迁徙；迁移", "migr(迁移)+ate→迁移"),
    "minimum": ("/ˈmɪnɪməm/", "n./adj.", "最小值；最小的", "minim(最小)+um→最小值"),
    "modify": ("/ˈmɒdɪfaɪ/", "v.", "修改；调整", "mod(方式)+ify→调整方式→修改"),
    "monitor": ("/ˈmɒnɪtər/", "v./n.", "监视；监控器", "monit(警告)+or→警告者→监控"),
    "mutual": ("/ˈmjuːtʃuəl/", "adj.", "相互的；共同的", "mut(交换)+ual→互相交换"),
    "negative": ("/ˈneɡətɪv/", "adj.", "负面的；消极的", "neg(否定)+ative→否定的"),
    "negotiate": ("/nɪˈɡəʊʃieɪt/", "v.", "谈判；协商", "neg(否定)+oti(闲暇)+ate→非闲暇→谈判"),
    "nevertheless": ("/ˌnevərðəˈles/", "adv.", "然而；不过", "never+the+less→尽管如此"),
    "numerous": ("/ˈnjuːmərəs/", "adj.", "许多的；大量的", "numer(数字)+ous→数量多"),
    "objective": ("/əbˈdʒektɪv/", "n./adj.", "目标；客观的", "ob+ject(投)+ive→投向目标→客观"),
    "oblige": ("/əˈblaɪdʒ/", "v.", "迫使；使感激", "ob+lige(绑)→绑住→迫使"),
    "obtain": ("/əbˈteɪn/", "v.", "获得；得到", "ob+tain(拿住)→拿到→获得"),
    "occupy": ("/ˈɒkjupaɪ/", "v.", "占据；占领", "oc+cupy(抓取)→抓住→占据"),
    "opponent": ("/əˈpəʊnənt/", "n.", "对手；反对者", "op+pon(放置)+ent→放到对面→对手"),
    "opportunity": ("/ˌɒpəˈtjuːnəti/", "n.", "机会；时机", "op+port(港口)+unity→到港口→机会"),
    "orient": ("/ˈɔːrient/", "v./n.", "使适应；东方", "ori(升起)+ent→太阳升起→东方"),
    "overwhelm": ("/ˌəʊvərˈwelm/", "v.", "压倒；淹没", "over+whelm(压倒)→压倒"),
    "participate": ("/pɑːrˈtɪsɪpeɪt/", "v.", "参加；参与", "part(部分)+cip(拿)+ate→拿一部分→参与"),
    "perceive": ("/pərˈsiːv/", "v.", "感知；察觉", "per+ceive(拿取)→完全拿到→感知"),
    "permanent": ("/ˈpɜːrmənənt/", "adj.", "永久的；长期的", "per+man(停留)+ent→一直停留→永久"),
    "perspective": ("/pərˈspektɪv/", "n.", "视角；观点", "per+spect(看)+ive→看透→视角"),
    "phenomenon": ("/fɪˈnɒmɪnən/", "n.", "现象", "pheno(显示)+menon→显示出来的→现象"),
    "philosophy": ("/fɪˈlɒsəfi/", "n.", "哲学", "philo(爱)+sophy(智慧)→爱智慧→哲学"),
    "potential": ("/pəˈtenʃl/", "adj./n.", "潜在的；潜力", "potent(力量)+ial→有力量的→潜力"),
    "precise": ("/prɪˈsaɪs/", "adj.", "精确的", "pre+cise(切)→提前切好→精确"),
    "predict": ("/prɪˈdɪkt/", "v.", "预测；预言", "pre+dict(说)→提前说→预测"),
    "prejudice": ("/ˈpredʒudɪs/", "n.", "偏见；歧视", "pre+judice(判断)→预先判断→偏见"),
    "preliminary": ("/prɪˈlɪmɪnəri/", "adj.", "初步的；预备的", "pre+limin(门槛)+ary→在门槛之前→初步"),
    "prescribe": ("/prɪˈskraɪb/", "v.", "规定；开处方", "pre+scribe(写)→提前写好→规定"),
    "preserve": ("/prɪˈzɜːrv/", "v.", "保存；保护", "pre+serve(保持)→提前保持→保存"),
    "prevail": ("/prɪˈveɪl/", "v.", "盛行；占优势", "pre+vail(强大)→非常强大→占优势"),
    "primitive": ("/ˈprɪmɪtɪv/", "adj.", "原始的；简单的", "prim(第一)+itive→第一的→原始"),
    "principle": ("/ˈprɪnsəpl/", "n.", "原理；原则", "prin(第一)+cip(拿)+le→首要→原则"),
    "priority": ("/praɪˈɒrəti/", "n.", "优先；优先级", "prior(在先)+ity→优先"),
    "proceed": ("/prəˈsiːd/", "v.", "继续；进行", "pro+ceed(走)→向前走→继续"),
    "prominent": ("/ˈprɒmɪnənt/", "adj.", "突出的；著名的", "pro+min(突出)+ent→突出"),
    "promote": ("/prəˈməʊt/", "v.", "促进；晋升", "pro+mote(移动)→向前移动→促进"),
    "propose": ("/prəˈpəʊz/", "v.", "提议；建议", "pro+pose(放置)→向前放→提议"),
    "prospect": ("/ˈprɒspekt/", "n.", "前景；展望", "pro+spect(看)→向前看→前景"),
    "psychology": ("/saɪˈkɒlədʒi/", "n.", "心理学", "psycho(心灵)+logy(学科)→心理学"),
    "purchase": ("/ˈpɜːrtʃəs/", "v./n.", "购买", "pur+chase(追逐)→追逐→购买"),
    "pursue": ("/pəˈsjuː/", "v.", "追求；追赶", "pur+sue(跟随)→跟随→追求"),
    "random": ("/ˈrændəm/", "adj.", "随机的；任意的", "rand(边缘)+om→到处→随机"),
    "rational": ("/ˈræʃnəl/", "adj.", "理性的；合理的", "ration(理性)+al→理性的"),
    "recommend": ("/ˌrekəˈmend/", "v.", "推荐；建议", "re+commend(委托)→反复委托→推荐"),
    "reconcile": ("/ˈrekənsaɪl/", "v.", "调和；和解", "re+concile(安抚)→再次安抚→和解"),
    "reinforce": ("/ˌriːɪnˈfɔːrs/", "v.", "加强；加固", "re+in+force(力量)→再次加力→加强"),
    "relevant": ("/ˈreləvənt/", "adj.", "相关的", "re+lev(举起)+ant→举起来的→相关"),
    "reluctant": ("/rɪˈlʌktənt/", "adj.", "不情愿的；勉强的", "re+luct(斗争)+ant→反向斗争→勉强"),
    "remedy": ("/ˈremədi/", "n./v.", "补救；治疗", "re+med(治愈)+y→治愈→补救"),
    "render": ("/ˈrendər/", "v.", "使成为；提供；渲染", "ren(回)+der(给予)→给予→使成为"),
    "representative": ("/ˌreprɪˈzentətɪv/", "n./adj.", "代表；有代表性的", "re+present(呈现)+ative→代表"),
    "reproduce": ("/ˌriːprəˈdjuːs/", "v.", "复制；繁殖", "re+produce(生产)→再生产→复制"),
    "reputation": ("/ˌrepjuˈteɪʃn/", "n.", "名声；声誉", "re+put(思考)+ation→反复思考→名声"),
    "resemble": ("/rɪˈzembl/", "v.", "类似；像", "re+semble(相似)→相似"),
    "reserve": ("/rɪˈzɜːrv/", "v./n.", "保留；储备", "re+serve(保持)→保持→保留"),
    "resign": ("/rɪˈzaɪn/", "v.", "辞职；放弃", "re+sign(标记)→重新标记→放弃"),
    "resolve": ("/rɪˈzɒlv/", "v.", "解决；下决心", "re+solve(解开)→解开→解决"),
    "restore": ("/rɪˈstɔːr/", "v.", "恢复；修复", "re+store(建立)→重新建立→恢复"),
    "restrain": ("/rɪˈstreɪn/", "v.", "抑制；限制", "re+strain(拉紧)→拉紧→抑制"),
    "reveal": ("/rɪˈviːl/", "v.", "揭示；透露", "re+veal(面纱)→揭开面纱→揭示"),
    "reverse": ("/rɪˈvɜːrs/", "v./adj.", "反转；相反的", "re+verse(转)→反转"),
    "revolution": ("/ˌrevəˈluːʃn/", "n.", "革命；旋转", "re+volut(转)+ion→翻转→革命"),
    "sacrifice": ("/ˈsækrɪfaɪs/", "v./n.", "牺牲；献祭", "sacri(神圣)+fice(做)→做神圣之事→牺牲"),
    "scrutiny": ("/ˈskruːtəni/", "n.", "仔细审查", "scrut(检查)+iny→仔细检查"),
    "sensitive": ("/ˈsensɪtɪv/", "adj.", "敏感的；灵敏的", "sens(感觉)+itive→有感觉→敏感"),
    "simulate": ("/ˈsɪmjuleɪt/", "v.", "模拟；仿真", "simul(相似)+ate→使相似→模拟"),
    "simultaneous": ("/ˌsɪmlˈteɪniəs/", "adj.", "同时的", "simul(相同)+taneous→同时"),
    "sophisticated": ("/səˈfɪstɪkeɪtɪd/", "adj.", "复杂的；精密的；世故的", "soph(智慧)+isticated→聪明的→精密"),
    "speculate": ("/ˈspekjuleɪt/", "v.", "推测；投机", "spec(看)+ulate→看→推测"),
    "spontaneous": ("/spɒnˈteɪniəs/", "adj.", "自发的；自然的", "spont(自愿)+aneous→自发的"),
    "statistics": ("/stəˈtɪstɪks/", "n.", "统计学；统计", "stat(状态)+istics→统计学"),
    "stimulate": ("/ˈstɪmjuleɪt/", "v.", "刺激；激励", "stimul(刺)+ate→刺激"),
    "strategy": ("/ˈstrætədʒi/", "n.", "策略；战略", "strat(军队)+egy→军队策略→战略"),
    "subordinate": ("/səˈbɔːrdɪnət/", "adj./n.", "下属的；下级", "sub+ordin(顺序)+ate→在顺序之下→下级"),
    "subsequent": ("/ˈsʌbsɪkwənt/", "adj.", "随后的", "sub+sequ(跟随)+ent→跟在下面→随后"),
    "substantial": ("/səbˈstænʃl/", "adj.", "大量的；重大的；实质的", "sub+stant(站立)+ial→站在下面→实质"),
    "substitute": ("/ˈsʌbstɪtjuːt/", "v./n.", "替代；替代品", "sub+stitute(建立)→建立在下→替代"),
    "sufficient": ("/səˈfɪʃnt/", "adj.", "足够的；充分的", "suf+fic(做)+ient→做够了→足够"),
    "superficial": ("/ˌsuːpərˈfɪʃl/", "adj.", "表面的；肤浅的", "super+fic(脸)+ial→脸上的→表面"),
    "superior": ("/suːˈpɪriər/", "adj.", "优越的；上级的", "super(上)+ior→在上面的→上级"),
    "supplement": ("/ˈsʌplɪment/", "n./v.", "补充；增补", "sup+ple(填满)+ment→补充填满"),
    "surrender": ("/səˈrendər/", "v.", "投降；屈服", "sur+render(给予)→上交→投降"),
    "suspend": ("/səˈspend/", "v.", "暂停；悬挂", "sus+pend(悬挂)→悬挂→暂停"),
    "suspicious": ("/səˈspɪʃəs/", "adj.", "怀疑的；可疑的", "sus+spic(看)+ious→向下看→怀疑"),
    "sustainable": ("/səˈsteɪnəbl/", "adj.", "可持续的", "sustain(维持)+able→可持续"),
    "symbolic": ("/sɪmˈbɒlɪk/", "adj.", "象征的；符号的", "symbol(符号)+ic→符号的"),
    "symptom": ("/ˈsɪmptəm/", "n.", "症状；征兆", "sym+ptom(落下)→一起落下→症状"),
    "synthetic": ("/sɪnˈθetɪk/", "adj.", "综合的；合成的", "syn+thet(放置)+ic→放在一起→合成"),
    "tackle": ("/ˈtækl/", "v./n.", "处理； tackle", "tack(抓住)+le→抓住→处理"),
    "tendency": ("/ˈtendənsi/", "n.", "倾向；趋势", "tend(趋向)+ency→倾向"),
    "terminate": ("/ˈtɜːrmɪneɪt/", "v.", "终止；结束", "termin(界限)+ate→到界限→终止"),
    "tolerance": ("/ˈtɒlərəns/", "n.", "容忍；耐受性", "toler(容忍)+ance→容忍"),
    "transform": ("/trænsˈfɔːrm/", "v.", "转变；变换", "trans+form(形状)→改变形状→转变"),
    "transit": ("/ˈtrænzɪt/", "n./v.", "运输；经过", "trans+it(走)→走过→经过"),
    "trigger": ("/ˈtrɪɡər/", "v./n.", "触发；扳机", "trig(拉)+ger→拉→触发"),
    "ultimate": ("/ˈʌltɪmət/", "adj.", "最终的；终极的", "ultim(最后)+ate→最后→最终"),
    "undergo": ("/ˌʌndərˈɡəʊ/", "v.", "经历；遭受", "under+go(走)→在下面走→经历"),
    "underlying": ("/ˌʌndərˈlaɪɪŋ/", "adj.", "潜在的；根本的", "under+lying(躺)→躺在下面→潜在"),
    "undertake": ("/ˌʌndərˈteɪk/", "v.", "承担；从事", "under+take(拿)→从下面拿→承担"),
    "unique": ("/juˈniːk/", "adj.", "独特的；唯一的", "uni(一)+que→唯一的→独特"),
    "universal": ("/ˌjuːnɪˈvɜːrsl/", "adj.", "普遍的；通用的", "uni+vers(转)+al→统一转向→普遍"),
    "utilize": ("/ˈjuːtɪlaɪz/", "v.", "利用；使用", "util(用)+ize→利用"),
    "valid": ("/ˈvælɪd/", "adj.", "有效的；合理的", "val(价值)+id→有价值的→有效"),
    "verify": ("/ˈverɪfaɪ/", "v.", "验证；核实", "ver(真实)+ify→使真实→验证"),
    "version": ("/ˈvɜːrʒn/", "n.", "版本；说法", "vers(转)+ion→转出来→版本"),
    "virtual": ("/ˈvɜːrtʃuəl/", "adj.", "虚拟的；实质的", "virtu(美德)+al→虚拟的"),
    "visible": ("/ˈvɪzəbl/", "adj.", "可见的；明显的", "vis(看)+ible(可…的)→可见"),
    "vital": ("/ˈvaɪtl/", "adj.", "至关重要的", "vit(生命)+al→关乎生命→至关重要"),
    "voluntary": ("/ˈvɒləntri/", "adj.", "自愿的", "volunt(意愿)+ary→自愿"),
    "vulnerable": ("/ˈvʌlnərəbl/", "adj.", "脆弱的；易受伤的", "vulner(伤口)+able→易受伤→脆弱"),
    "welfare": ("/ˈwelfeər/", "n.", "福利；幸福", "wel(好)+fare(状态)→良好状态→福利"),
    "widespread": ("/ˈwaɪdspred/", "adj.", "广泛的；普遍的", "wide(广)+spread(散布)→广泛"),
    "worthwhile": ("/ˌwɜːrθˈwaɪl/", "adj.", "值得的", "worth(价值)+while(时间)→值得花时间"),
    "yield": ("/jiːld/", "v./n.", "屈服；产出；产量", "yield(给予)→产出"),

    # ────────── 测绘/遥感/GIS/Navigation 专业术语 ──────────
    "aerial": ("/ˈeəriəl/", "adj./n.", "空中的；天线", "aer(空气)+ial→空中的"),
    "altimeter": ("/ˈæltɪmiːtər/", "n.", "高度计", "alti(高)+meter(测量)→高度计"),
    "antenna": ("/ænˈtenə/", "n.", "天线", "antenna(帆桁)→天线(形状像)"),
    "aperture": ("/ˈæpərtʃər/", "n.", "孔径；光圈", "aper(打开)+ture→开口→孔径"),
    "azimuth": ("/ˈæzɪməθ/", "n.", "方位角", "az(方向)+imuth→方位角"),
    "backscatter": ("/ˈbækskætər/", "n./v.", "后向散射", "back+scatter(散射)→后向散射"),
    "baseline": ("/ˈbeɪslaɪn/", "n.", "基线", "base(基础)+line(线)→基线"),
    "bathymetry": ("/bəˈθɪmətri/", "n.", "水深测量", "bathy(深)+metry(测量)→水深测量"),
    "bearing": ("/ˈbeərɪŋ/", "n.", "方位；轴承", "bear(承载)+ing→承载方向→方位"),
    "benchmark": ("/ˈbentʃmɑːrk/", "n.", "基准点；基准", "bench+mark→基准标记→基准"),
    "calibrate": ("/ˈkælɪbreɪt/", "v.", "标定；校准", "calibr(刻度)+ate→标定"),
    "cartography": ("/kɑːrˈtɒɡrəfi/", "n.", "地图制图学", "carto(地图)+graphy(绘制)→地图学"),
    "centroid": ("/ˈsentrɔɪd/", "n.", "质心；形心", "centr(中心)+oid(体)→质心"),
    "clinometer": ("/klaɪˈnɒmɪtər/", "n.", "测斜仪", "clino(倾斜)+meter(测量)→测斜仪"),
    "collimate": ("/ˈkɒlɪmeɪt/", "v.", "准直；瞄准", "col+lim(线)+ate→共线→准直"),
    "contour": ("/ˈkɒntʊr/", "n.", "等高线；轮廓", "con+tour(转)→转一圈→轮廓"),
    "datum": ("/ˈdeɪtəm/", "n.", "基准；数据", "dat(给予)+um→给定的→基准"),
    "declination": ("/ˌdeklɪˈneɪʃn/", "n.", "偏角；磁偏角；赤纬", "de+clin(倾斜)+ation→倾斜"),
    "deformation": ("/ˌdiːfɔːrˈmeɪʃn/", "n.", "变形", "de+form(形状)+ation→变形"),
    "demodulation": ("/diːˌmɒdʒuˈleɪʃn/", "n.", "解调", "de+modul(调节)+ation→解调"),
    "diffraction": ("/dɪˈfrækʃn/", "n.", "衍射", "dif+fract(打破)+ion→打破→衍射"),
    "displacement": ("/dɪsˈpleɪsmənt/", "n.", "位移；置换", "dis+place(放置)+ment→位移"),
    "doppler": ("/ˈdɒplər/", "n.", "多普勒(效应)", "多普勒(人名)→多普勒效应"),
    "elevation": ("/ˌelɪˈveɪʃn/", "n.", "高程；海拔", "e+lev(举起)+ation→举起→高程"),
    "ellipsoid": ("/ɪˈlɪpsɔɪd/", "n.", "椭球体", "ellips(椭圆)+oid(体)→椭球体"),
    "ephemeris": ("/ɪˈfemərɪs/", "n.", "星历", "ephemer(一日)+is→每日数据→星历"),
    "epoch": ("/ˈiːpɒk/", "n.", "历元；时代", "epoch(停止点)→历元"),
    "geodesy": ("/dʒiːˈɒdɪsi/", "n.", "大地测量学", "geo(地球)+desy(划分)→大地测量"),
    "geoid": ("/ˈdʒiːɔɪd/", "n.", "大地水准面", "geo(地球)+oid(体)→大地水准面"),
    "georeference": ("/ˌdʒiːəʊˈrefrəns/", "v.", "地理配准", "geo+reference(参考)→地理配准"),
    "geospatial": ("/ˌdʒiːəʊˈspeɪʃl/", "adj.", "地理空间的", "geo+spatial(空间的)→地理空间"),
    "gnss": ("/dʒiː en es es/", "n.", "全球导航卫星系统", "Global Navigation Satellite System"),
    "gradiometer": ("/ˌɡreɪdiˈɒmɪtər/", "n.", "梯度仪", "gradi(梯度)+meter→梯度仪"),
    "gravimetry": ("/ɡrəˈvɪmətri/", "n.", "重力测量", "gravi(重力)+metry(测量)→重力测量"),
    "gyroscope": ("/ˈdʒaɪrəskəʊp/", "n.", "陀螺仪", "gyro(旋转)+scope(观察)→陀螺仪"),
    "hydrography": ("/haɪˈdrɒɡrəfi/", "n.", "水文测量", "hydro(水)+graphy(绘制)→水文测量"),
    "inclination": ("/ˌɪnklɪˈneɪʃn/", "n.", "倾角；倾斜", "in+clin(倾斜)+ation→倾斜"),
    "interferometry": ("/ˌɪntərfɪˈrɒmətri/", "n.", "干涉测量", "interfer(干涉)+ometry→干涉测量"),
    "ionosphere": ("/aɪˈɒnəsfɪər/", "n.", "电离层", "ion(离子)+sphere(层)→电离层"),
    "kinematic": ("/ˌkɪnɪˈmætɪk/", "adj.", "运动学的", "kinema(运动)+tic→运动学的"),
    "laser": ("/ˈleɪzər/", "n.", "激光", "Light Amplification缩写→激光"),
    "latitude": ("/ˈlætɪtjuːd/", "n.", "纬度", "lat(宽)+itude→宽度→纬度"),
    "levelling": ("/ˈlevəlɪŋ/", "n.", "水准测量", "level(水平)+ing→水准测量"),
    "lidar": ("/ˈlaɪdɑːr/", "n.", "激光雷达", "Light Detection And Ranging→激光雷达"),
    "longitude": ("/ˈlɒndʒɪtjuːd/", "n.", "经度", "long(长)+itude→长度→经度"),
    "magnetometer": ("/ˌmæɡnɪˈtɒmɪtər/", "n.", "磁力计", "magneto(磁)+meter→磁力计"),
    "meridian": ("/məˈrɪdiən/", "n.", "子午线", "meri(中午)+dian→正午太阳→子午线"),
    "metrology": ("/mɪˈtrɒlədʒi/", "n.", "计量学", "metro(测量)+logy→计量学"),
    "monocular": ("/məˈnɒkjʊlər/", "adj.", "单目的", "mono(单一)+ocular(眼睛)→单目"),
    "multispectral": ("/ˌmʌltiˈspektrəl/", "adj.", "多光谱的", "multi+spectral(光谱的)→多光谱"),
    "nadir": ("/ˈneɪdɪər/", "n.", "天底点", "nadir(对应点)→天底点"),
    "navigation": ("/ˌnævɪˈɡeɪʃn/", "n.", "导航", "nav(船)+ig+ation→驾驶船→导航"),
    "observatory": ("/əbˈzɜːrvətri/", "n.", "观测站；天文台", "observe(观察)+atory→观测站"),
    "occlusion": ("/əˈkluːʒn/", "n.", "遮挡", "oc+clus(关)+ion→关闭→遮挡"),
    "orthometric": ("/ˌɔːrθəˈmetrɪk/", "adj.", "正高的", "ortho(正)+metric(测量)→正高"),
    "orthophoto": ("/ˈɔːrθəˌfəʊtəʊ/", "n.", "正射影像", "ortho(正)+photo(照片)→正射影像"),
    "parallax": ("/ˈpærəlæks/", "n.", "视差", "par+allax(变换)→平行变换→视差"),
    "photogrammetry": ("/ˌfəʊtəˈɡræmɪtri/", "n.", "摄影测量", "photo+gram+metry→摄影测量"),
    "pixel": ("/ˈpɪksl/", "n.", "像素", "pix(图片)+el(元素)→像素"),
    "planimetry": ("/plæˈnɪmɪtri/", "n.", "平面测量", "plani(平面)+metry→平面测量"),
    "polarization": ("/ˌpəʊləraɪˈzeɪʃn/", "n.", "偏振", "polar(极)+ization→偏振"),
    "radiometer": ("/ˌreɪdiˈɒmɪtər/", "n.", "辐射计", "radio(辐射)+meter→辐射计"),
    "radiosonde": ("/ˈreɪdiəʊsɒnd/", "n.", "无线电探空仪", "radio+sonde(探测)→探空仪"),
    "reflectance": ("/rɪˈflektəns/", "n.", "反射率", "re+flect(弯)+ance→弯回→反射"),
    "refraction": ("/rɪˈfrækʃn/", "n.", "折射", "re+fract(打破)+ion→打破→折射"),
    "registration": ("/ˌredʒɪˈstreɪʃn/", "n.", "配准；注册", "re+gistr(记录)+ation→记录→配准"),
    "resection": ("/rɪˈsekʃn/", "n.", "后方交会", "re+sect(切)+ion→切回→后方交会"),
    "resolution": ("/ˌrezəˈluːʃn/", "n.", "分辨率；解析", "re+solut(解开)+ion→解开→分辨率"),
    "scatterometer": ("/ˌskætəˈrɒmɪtər/", "n.", "散射计", "scatter(散射)+meter→散射计"),
    "seismometer": ("/saɪzˈmɒmɪtər/", "n.", "地震仪", "seismo(地震)+meter→地震仪"),
    "spectrometer": ("/spekˈtrɒmɪtər/", "n.", "光谱仪", "spectro(光谱)+meter→光谱仪"),
    "stadia": ("/ˈsteɪdiə/", "n.", "视距测量", "stad(站立)+ia→视距"),
    "stereoscopic": ("/ˌsteriəˈskɒpɪk/", "adj.", "立体的", "stereo(立体)+scopic(看)→立体"),
    "subsidence": ("/səbˈsaɪdns/", "n.", "沉降；下沉", "sub+sid(坐)+ence→向下坐→沉降"),
    "telemetry": ("/tɪˈlemɪtri/", "n.", "遥测", "tele(远)+metry(测量)→遥测"),
    "theodolite": ("/θiˈɒdəlaɪt/", "n.", "经纬仪", "theod(观看)+olite→经纬仪"),
    "topography": ("/təˈpɒɡrəfi/", "n.", "地形学；地势", "topo(地方)+graphy(绘制)→地形学"),
    "topology": ("/təˈpɒlədʒi/", "n.", "拓扑学", "topo(地方)+logy(学科)→拓扑"),
    "transducer": ("/trænzˈdjuːsər/", "n.", "传感器；换能器", "trans+duce(引导)+er→转换器"),
    "triangulation": ("/traɪˌæŋɡjuˈleɪʃn/", "n.", "三角测量", "tri(三)+angul(角)+ation→三角测量"),
    "trilateration": ("/traɪˌlætəˈreɪʃn/", "n.", "三边测量", "tri(三)+later(边)+ation→三边测量"),
    "troposphere": ("/ˈtrɒpəsfɪər/", "n.", "对流层", "tropo(转向)+sphere(层)→对流层"),
    "zenith": ("/ˈzenɪθ/", "n.", "天顶", "zenith(路径)→天顶"),

    # ────────── CET-6 扩展 + 学术写作高频 ──────────
    "absorption": ("/əbˈzɔːrpʃn/", "n.", "吸收；专注", "ab+sorpt(吸)+ion→吸收"),
    "abstraction": ("/æbˈstrækʃn/", "n.", "抽象；提取", "abs+tract(拉)+ion→抽象"),
    "acceleration": ("/əkˌseləˈreɪʃn/", "n.", "加速(度)", "ac+celer(快速)+ation→加速"),
    "accumulate": ("/əˈkjuːmjuleɪt/", "v.", "积累；积聚", "ac+cumul(堆积)+ate→积累"),
    "adolescence": ("/ˌædəˈlesns/", "n.", "青春期", "adol(成年)+escence(开始)→青春期"),
    "affirm": ("/əˈfɜːrm/", "v.", "确认；肯定", "af+firm(坚定)→使坚定→确认"),
    "aggregate": ("/ˈæɡrɪɡət/", "v./n./adj.", "聚集；合计的", "ag+greg(群体)+ate→聚集"),
    "algorithm": ("/ˈælɡərɪðəm/", "n.", "算法", "algor(数字)+ithm→算法"),
    "alignment": ("/əˈlaɪnmənt/", "n.", "对齐；对准", "a+lign(线)+ment→排成线→对齐"),
    "allocation": ("/ˌæləˈkeɪʃn/", "n.", "分配；配置", "al+loc(位置)+ation→分配"),
    "altitude": ("/ˈæltɪtjuːd/", "n.", "海拔；高度", "alti(高)+tude→高度"),
    "amplitude": ("/ˈæmplɪtjuːd/", "n.", "振幅；幅度", "ampl(大)+itude→幅度"),
    "annotate": ("/ˈænəʊteɪt/", "v.", "注释；注解", "an+not(标记)+ate→注释"),
    "anomaly": ("/əˈnɒməli/", "n.", "异常；反常", "a+nom(法则)+aly→不合法则→异常"),
    "asymptotic": ("/ˌæsɪmpˈtɒtɪk/", "adj.", "渐进的", "a+sympt(落)+otic→不落下→渐进"),
    "attenuation": ("/əˌtenjuˈeɪʃn/", "n.", "衰减", "at+tenu(细)+ation→变细→衰减"),
    "bandwidth": ("/ˈbændwɪdθ/", "n.", "带宽", "band(带)+width(宽)→带宽"),
    "beamforming": ("/ˈbiːmfɔːrmɪŋ/", "n.", "波束赋形", "beam(波束)+forming(形成)→波束赋形"),
    "bias": ("/ˈbaɪəs/", "n.", "偏差；偏见", "bias(斜的)→偏差"),
    "calibration": ("/ˌkælɪˈbreɪʃn/", "n.", "标定；校准", "calibr(刻度)+ation→标定"),
    "clutter": ("/ˈklʌtər/", "n.", "杂波；杂乱", "clutt(凝结)+er→杂乱"),
    "coefficient": ("/ˌkəʊɪˈfɪʃnt/", "n.", "系数", "co+efficient(效率)→系数"),
    "coherence": ("/kəʊˈhɪərəns/", "n.", "相干性；一致性", "co+her(黏附)+ence→黏在一起→相干"),
    "complexity": ("/kəmˈpleksəti/", "n.", "复杂性", "com+plex(折叠)+ity→复杂"),
    "compression": ("/kəmˈpreʃn/", "n.", "压缩", "com+press(压)+ion→压缩"),
    "computation": ("/ˌkɒmpjuˈteɪʃn/", "n.", "计算", "com+put(思考)+ation→计算"),
    "conductivity": ("/ˌkɒndʌkˈtɪvəti/", "n.", "导电性；传导率", "conduct(传导)+ivity→传导率"),
    "configuration": ("/kənˌfɪɡəˈreɪʃn/", "n.", "配置；构型", "con+figur(形状)+ation→配置"),
    "conjugate": ("/ˈkɒndʒʊɡət/", "v./adj.", "共轭；结合", "con+jug(连接)+ate→共轭"),
    "consistency": ("/kənˈsɪstənsi/", "n.", "一致性", "con+sist(站立)+ency→一致性"),
    "constraint": ("/kənˈstreɪnt/", "n.", "约束；限制", "con+straint(拉紧)→约束"),
    "convergence": ("/kənˈvɜːrdʒəns/", "n.", "收敛；汇聚", "con+verge(转)+ence→转到一起→收敛"),
    "convolution": ("/ˌkɒnvəˈluːʃn/", "n.", "卷积", "con+volut(卷)+ion→卷在一起→卷积"),
    "covariance": ("/kəʊˈveəriəns/", "n.", "协方差", "co+variance(方差)→协方差"),
    "criterion": ("/kraɪˈtɪəriən/", "n.", "标准；准则", "crit(判断)+erion→判断标准"),
    "decomposition": ("/ˌdiːkɒmpəˈzɪʃn/", "n.", "分解", "de+com+pos(放置)+ition→分解"),
    "deconvolution": ("/diːˌkɒnvəˈluːʃn/", "n.", "反卷积", "de+convolution(卷积)→反卷积"),
    "determinant": ("/dɪˈtɜːrmɪnənt/", "n.", "行列式；决定因素", "de+termin(界限)+ant→决定因素"),
    "deviation": ("/ˌdiːviˈeɪʃn/", "n.", "偏差；偏离", "de+vi(路)+ation→偏离道路→偏差"),
    "discrete": ("/dɪˈskriːt/", "adj.", "离散的", "dis+crete(区分)→分开→离散"),
    "distribution": ("/ˌdɪstrɪˈbjuːʃn/", "n.", "分布；分配", "dis+tribute(给予)+ion→分布"),
    "divergence": ("/daɪˈvɜːrdʒəns/", "n.", "发散；分歧", "di+verge(转)+ence→转开→发散"),
    "eigenvalue": ("/ˈaɪɡənˌvæljuː/", "n.", "特征值", "eigen(自己的)+value(值)→特征值"),
    "emission": ("/iˈmɪʃn/", "n.", "发射；排放", "e+miss(发送)+ion→发送出去→发射"),
    "entropy": ("/ˈentrəpi/", "n.", "熵", "en+tropy(转变)→能量转变→熵"),
    "ergodic": ("/ɜːrˈɡɒdɪk/", "adj.", "遍历的", "ergo(工作)+dic→遍历"),
    "estimation": ("/ˌestɪˈmeɪʃn/", "n.", "估计；估算", "estim(价值)+ation→估计"),
    "excitation": ("/ˌeksaɪˈteɪʃn/", "n.", "激发；激励", "ex+cit(唤起)+ation→唤起→激发"),
    "expectation": ("/ˌekspekˈteɪʃn/", "n.", "期望；预期", "ex+pect(看)+ation→期望"),
    "extrapolation": ("/ɪkˌstræpəˈleɪʃn/", "n.", "外推；推断", "extra+pol(推)+ation→向外推→外推"),
    "factorial": ("/fækˈtɔːriəl/", "n./adj.", "阶乘", "factor(因子)+ial→阶乘"),
    "feedback": ("/ˈfiːdbæk/", "n.", "反馈", "feed(喂养)+back(回)→喂回→反馈"),
    "filter": ("/ˈfɪltər/", "n./v.", "滤波器；过滤", "filt(滤)+er→滤波器"),
    "fusion": ("/ˈfjuːʒn/", "n.", "融合", "fus(融化)+ion→融合"),
    "gaussian": ("/ˈɡaʊsiən/", "adj.", "高斯的", "Gauss(高斯)+ian→高斯的"),
    "gradient": ("/ˈɡreɪdiənt/", "n.", "梯度", "gradi(步)+ent→逐步→梯度"),
    "heuristic": ("/hjuˈrɪstɪk/", "adj.", "启发式的", "heur(发现)+istic→发现→启发"),
    "histogram": ("/ˈhɪstəɡræm/", "n.", "直方图", "histo(组织)+gram(图)→直方图"),
    "hypothesis": ("/haɪˈpɒθɪsɪs/", "n.", "假设；假说", "hypo(下面)+thesis(放置)→放在下面→假设"),
    "identification": ("/aɪˌdentɪfɪˈkeɪʃn/", "n.", "识别；鉴定", "ident(相同)+ification→识别"),
    "impedance": ("/ɪmˈpiːdns/", "n.", "阻抗", "im+ped(脚)+ance→碍脚→阻抗"),
    "impulse": ("/ˈɪmpʌls/", "n.", "脉冲；冲动", "im+pulse(推动)→推动→脉冲"),
    "inductance": ("/ɪnˈdʌktəns/", "n.", "电感", "in+duct(引导)+ance→电感"),
    "inertial": ("/ɪˈnɜːrʃl/", "adj.", "惯性的", "inert(惰性)+ial→惯性的"),
    "inference": ("/ˈɪnfərəns/", "n.", "推理；推断", "in+fer(带来)+ence→带进来→推断"),
    "initialization": ("/ɪˌnɪʃəlaɪˈzeɪʃn/", "n.", "初始化", "initial(初始)+ization→初始化"),
    "insar": ("/ˈɪnsɑːr/", "n.", "合成孔径雷达干涉测量", "Interferometric SAR→InSAR"),
    "integration": ("/ˌɪntɪˈɡreɪʃn/", "n.", "积分；集成", "integr(完整)+ation→积分"),
    "interpolation": ("/ɪnˌtɜːrpəˈleɪʃn/", "n.", "插值", "inter+pol(推)+ation→在中间推→插值"),
    "invariant": ("/ɪnˈveəriənt/", "adj.", "不变的；不变量", "in+vary(变化)+ant→不变"),
    "inversion": ("/ɪnˈvɜːrʒn/", "n.", "反演；反转", "in+vers(转)+ion→反转"),
    "iteration": ("/ˌɪtəˈreɪʃn/", "n.", "迭代", "iter(再次)+ation→反复→迭代"),
    "jacobian": ("/dʒəˈkəʊbiən/", "n.", "雅可比矩阵", "Jacobi(雅可比)+an→雅可比"),
    "kalman": ("/ˈkælmən/", "n.", "卡尔曼", "Kalman(人名)→卡尔曼滤波"),
    "kernel": ("/ˈkɜːrnl/", "n.", "核；内核", "kern(核心)+el(小)→内核"),
    "kinematics": ("/ˌkɪnɪˈmætɪks/", "n.", "运动学", "kinema(运动)+tics→运动学"),
    "kurtosis": ("/kɜːrˈtəʊsɪs/", "n.", "峰度", "kurt(弯曲)+osis→峰度"),
    "lagrangian": ("/ləˈɡrændʒiən/", "adj./n.", "拉格朗日的", "Lagrange(拉格朗日)+ian"),
    "laplacian": ("/ləˈpleɪʃən/", "n.", "拉普拉斯算子", "Laplace(拉普拉斯)+ian"),
    "latency": ("/ˈleɪtənsi/", "n.", "延迟；潜伏", "lat(隐藏)+ency→潜伏→延迟"),
    "likelihood": ("/ˈlaɪklihʊd/", "n.", "似然；可能性", "likely(可能)+hood→似然"),
    "linearization": ("/ˌlɪniəraɪˈzeɪʃn/", "n.", "线性化", "linear(线性)+ization→线性化"),
    "magnitude": ("/ˈmæɡnɪtjuːd/", "n.", "量级；大小", "magn(大)+itude→量级"),
    "manifold": ("/ˈmænɪfəʊld/", "n.", "流形", "mani(多)+fold(折)→多层→流形"),
    "mapping": ("/ˈmæpɪŋ/", "n.", "制图；映射", "map(地图)+ing→制图"),
    "matrix": ("/ˈmeɪtrɪks/", "n.", "矩阵", "matr(母)+ix→母体→矩阵"),
    "maximum": ("/ˈmæksɪməm/", "n./adj.", "最大值", "maxim(最大)+um→最大值"),
    "mems": ("/memz/", "n.", "微机电系统", "Micro-Electro-Mechanical System→MEMS"),
    "modulation": ("/ˌmɒdʒuˈleɪʃn/", "n.", "调制", "modul(调节)+ation→调制"),
    "multipath": ("/ˈmʌltipæθ/", "n.", "多路径", "multi(多)+path(路径)→多路径"),
    "nonlinear": ("/nɒnˈlɪniər/", "adj.", "非线性的", "non(非)+linear(线性)→非线性"),
    "normalization": ("/ˌnɔːrməlaɪˈzeɪʃn/", "n.", "归一化", "normal(正常)+ization→归一化"),
    "observability": ("/əbˌzɜːrvəˈbɪləti/", "n.", "可观性", "observe(观察)+ability→可观性"),
    "optimization": ("/ˌɒptɪmaɪˈzeɪʃn/", "n.", "优化", "optim(最佳)+ization→优化"),
    "orbit": ("/ˈɔːrbɪt/", "n./v.", "轨道", "orb(圆)+it→轨道"),
    "oscillator": ("/ˈɒsɪleɪtər/", "n.", "振荡器", "oscill(摆动)+ator→振荡器"),
    "outlier": ("/ˈaʊtlaɪər/", "n.", "异常值；离群值", "out(外)+lier(躺)→异常值"),
    "parameter": ("/pəˈræmɪtər/", "n.", "参数", "para(旁)+meter(测量)→参数"),
    "perturbation": ("/ˌpɜːrtərˈbeɪʃn/", "n.", "扰动", "per+turb(搅动)+ation→扰动"),
    "phase": ("/feɪz/", "n.", "相位；阶段", "phas(显示)+e→相位"),
    "pipeline": ("/ˈpaɪplaɪn/", "n.", "流水线；管线", "pipe(管)+line(线)→流水线"),
    "polynomial": ("/ˌpɒliˈnəʊmiəl/", "adj./n.", "多项式的", "poly(多)+nomial(项)→多项式"),
    "prediction": ("/prɪˈdɪkʃn/", "n.", "预测", "pre+dict(说)+ion→预测"),
    "probability": ("/ˌprɒbəˈbɪləti/", "n.", "概率", "prob(证实)+ability→可能性→概率"),
    "propagation": ("/ˌprɒpəˈɡeɪʃn/", "n.", "传播", "pro+pag(传播)+ation→传播"),
    "quadratic": ("/kwɒˈdrætɪk/", "adj.", "二次的", "quadr(四/平方)+atic→二次"),
    "quantization": ("/ˌkwɒntaɪˈzeɪʃn/", "n.", "量化", "quant(数量)+ization→量化"),
    "radar": ("/ˈreɪdɑːr/", "n.", "雷达", "Radio Detection And Ranging→雷达"),
    "reconstruction": ("/ˌriːkənˈstrʌkʃn/", "n.", "重构", "re+construct(构建)+ion→重构"),
    "recursion": ("/rɪˈkɜːrʒn/", "n.", "递归", "re+curs(跑)+ion→跑回去→递归"),
    "reflector": ("/rɪˈflektər/", "n.", "反射器", "re+flect(弯)+or→反射器"),
    "regression": ("/rɪˈɡreʃn/", "n.", "回归", "re+gress(走)+ion→走回去→回归"),
    "regularization": ("/ˌreɡjʊləraɪˈzeɪʃn/", "n.", "正则化", "regular(规则)+ization→正则化"),
    "representation": ("/ˌreprɪzenˈteɪʃn/", "n.", "表示；代表", "re+present(呈现)+ation→表示"),
    "residual": ("/rɪˈzɪdʒuəl/", "n./adj.", "残差；剩余的", "re+sid(坐)+ual→坐在后面→残余"),
    "robustness": ("/rəʊˈbʌstnəs/", "n.", "鲁棒性；稳健性", "robust(强壮)+ness→鲁棒性"),
    "sampling": ("/ˈsɑːmplɪŋ/", "n.", "采样", "sample(样本)+ing→采样"),
    "sar": ("/sɑːr/", "n.", "合成孔径雷达", "Synthetic Aperture Radar→SAR"),
    "scalar": ("/ˈskeɪlər/", "n./adj.", "标量", "scal(尺度)+ar→标量"),
    "scattering": ("/ˈskætərɪŋ/", "n.", "散射", "scatter(散射)+ing→散射"),
    "segmentation": ("/ˌseɡmenˈteɪʃn/", "n.", "分割", "segment(部分)+ation→分割"),
    "skewness": ("/ˈskjuːnəs/", "n.", "偏度", "skew(偏)+ness→偏度"),
    "sonar": ("/ˈsəʊnɑːr/", "n.", "声呐", "Sound Navigation Ranging→声呐"),
    "spectrum": ("/ˈspektrəm/", "n.", "频谱；光谱", "spectr(看)+um→光谱"),
    "stability": ("/stəˈbɪləti/", "n.", "稳定性", "stab(站立)+ility→站得住→稳定"),
    "stochastic": ("/stəˈkæstɪk/", "adj.", "随机的", "stoch(猜测)+astic→随机"),
    "subspace": ("/ˈsʌbspeɪs/", "n.", "子空间", "sub(子)+space(空间)→子空间"),
    "symmetric": ("/sɪˈmetrɪk/", "adj.", "对称的", "sym+metr(测量)+ic→对称"),
    "theorem": ("/ˈθɪərəm/", "n.", "定理", "theor(观察)+em→定理"),
    "threshold": ("/ˈθreʃhəʊld/", "n.", "阈值；门槛", "thresh(打)+old→门槛→阈值"),
    "trajectory": ("/trəˈdʒektəri/", "n.", "轨迹", "tra+ject(投)+ory→投出去→轨迹"),
    "transformation": ("/ˌtrænsfərˈmeɪʃn/", "n.", "变换", "trans+form(形状)+ation→变换"),
    "uncertainty": ("/ʌnˈsɜːrtnti/", "n.", "不确定性", "un+certain(确定)+ty→不确定性"),
    "validation": ("/ˌvælɪˈdeɪʃn/", "n.", "验证；确认", "valid(有效)+ation→验证"),
    "variance": ("/ˈveəriəns/", "n.", "方差", "vari(变化)+ance→方差"),
    "vector": ("/ˈvektər/", "n.", "向量；矢量", "vect(携带)+or→向量"),
    "velocity": ("/vɪˈlɒsəti/", "n.", "速度", "veloc(快速)+ity→速度"),
    "waveform": ("/ˈweɪvfɔːrm/", "n.", "波形", "wave(波)+form(形)→波形"),
    "wavelength": ("/ˈweɪvleŋθ/", "n.", "波长", "wave(波)+length(长度)→波长"),
    "weighting": ("/ˈweɪtɪŋ/", "n.", "加权", "weight(权重)+ing→加权"),

    # ────────── CET-6 高分词组 (20+) ──────────
    "account for": ("/əˈkaʊnt fɔːr/", "phr.", "解释；占…比例", "account(说明)+for→解释"),
    "adhere to": ("/ədˈhɪər tuː/", "phr.", "坚持；遵守", "ad+here(黏)+to→黏住→坚持"),
    "bring about": ("/brɪŋ əˈbaʊt/", "phr.", "引起；导致", "bring+about→带来→引起"),
    "come up with": ("/kʌm ʌp wɪð/", "phr.", "想出；提出", "come+up+with→上来→想出"),
    "cope with": ("/kəʊp wɪð/", "phr.", "应对；处理", "cope(应对)+with→处理"),
    "deprive of": ("/dɪˈpraɪv ɒv/", "phr.", "剥夺", "de+prive(夺走)+of→剥夺"),
    "derive from": ("/dɪˈraɪv frɒm/", "phr.", "源自；来自", "de+rive(河)+from→从…来→源自"),
    "devote to": ("/dɪˈvəʊt tuː/", "phr.", "致力于；奉献", "de+vote(发誓)+to→发誓做→致力于"),
    "dispose of": ("/dɪˈspəʊz ɒv/", "phr.", "处理；处置", "dis+pose(放)+of→处理掉"),
    "end up": ("/end ʌp/", "phr.", "最终；以…告终", "end+up→结束→最终"),
    "give rise to": ("/ɡɪv raɪz tuː/", "phr.", "引起；导致", "give+rise+to→给升起→导致"),
    "in terms of": ("/ɪn tɜːrmz ɒv/", "phr.", "就…而言；在…方面", "in+terms+of→在…方面"),
    "interfere with": ("/ˌɪntərˈfɪr wɪð/", "phr.", "干涉；干扰", "inter+fere(打)+with→干涉"),
    "pertain to": ("/pərˈteɪn tuː/", "phr.", "关于；属于", "per+tain(拿住)+to→属于"),
    "put forward": ("/pʊt ˈfɔːrwərd/", "phr.", "提出；建议", "put+forward→向前放→提出"),
    "resort to": ("/rɪˈzɔːrt tuː/", "phr.", "诉诸；求助于", "re+sort(出去)+to→求助"),
    "set forth": ("/set fɔːrθ/", "phr.", "阐述；出发", "set+forth→出发→阐述"),
    "stem from": ("/stem frɒm/", "phr.", "起源于", "stem(茎)+from→从…来→起源于"),
    "take into account": ("/teɪk ˈɪntuː əˈkaʊnt/", "phr.", "考虑；顾及", "take+into+account→考虑"),
    "turn out": ("/tɜːrn aʊt/", "phr.", "结果是；证明是", "turn+out→转出来→结果"),
}

# ══════════════════════════════════════════════════════════════════════
# 词根词缀数据库 - 用于分析生词的构词法
# ══════════════════════════════════════════════════════════════════════

PREFIXES = {
    "a": "不/无/加强(abnormal, amoral)",
    "ab": "偏离/离开(abnormal, abuse)",
    "ad": "朝向/加强(adhere, adjust)",
    "anti": "反对/抗(antibody, anticlockwise)",
    "auto": "自己/自动(automatic, autonomous)",
    "bene": "好/善(benefit, benevolent)",
    "bi": "二/双(bicycle, bilateral)",
    "bio": "生命/生物(biology, biography)",
    "circum": "周围/环绕(circumstance, circumference)",
    "co": "共同/一起(cooperate, coordinate)",
    "col": "共同/一起(collaborate, colleague)",
    "com": "共同/一起/完全(combine, complex)",
    "con": "共同/一起/完全(connect, converge)",
    "contra": "反对/相反(contradict, contrast)",
    "de": "向下/除去/完全(decline, decompose)",
    "dia": "通过/之间(diagram, dialect)",
    "dis": "不/除去/分开(dislike, dismiss)",
    "e": "出/向外(emerge, emit)",
    "en": "使…/在…中(enforce, enable)",
    "ex": "出/向外/超出(export, exceed)",
    "extra": "超出/以外(extraordinary, extrasolar)",
    "fore": "前/预先(forecast, foresee)",
    "il": "不/无(illegal, illogical)",
    "im": "不/无/进入(impossible, import)",
    "in": "不/无/进入(incomplete, invade)",
    "inter": "之间/互相(international, interact)",
    "intra": "内部(intranet, intravenous)",
    "ir": "不/无(irregular, irresponsible)",
    "macro": "大/宏观(macroscopic, macroeconomics)",
    "mal": "坏/错误(malfunction, maltreat)",
    "micro": "小/微(microscope, microwave)",
    "mid": "中间(midnight, midway)",
    "mis": "错误(misunderstand, mislead)",
    "mono": "单一(monopoly, monotonous)",
    "multi": "多(multiple, multimedia)",
    "non": "不/非(nonsense, nonlinear)",
    "ob": "反对/阻碍(object, obstacle)",
    "out": "超过/向外(outcome, output)",
    "over": "过度/超过(overload, overlook)",
    "per": "贯穿/完全(perfect, permanent)",
    "poly": "多(polygon, polynomial)",
    "post": "后/之后(postpone, postgraduate)",
    "pre": "前/预先(preview, predict)",
    "pro": "向前/支持(progress, promote)",
    "re": "再次/返回(return, reproduce)",
    "semi": "半(semifinal, semiconductor)",
    "sub": "下/次/子(submarine, subset)",
    "super": "超/上(superior, supervise)",
    "sur": "超/上(surface, surpass)",
    "sym": "共同/相同(sympathy, symmetry)",
    "syn": "共同/相同(synthesis, synchronize)",
    "tele": "远(television, telemetry)",
    "trans": "跨越/转变(transfer, transform)",
    "tri": "三(triangle, triple)",
    "ultra": "超/极端(ultrasonic, ultraviolet)",
    "un": "不/相反(unable, undo)",
    "under": "下/不足(underline, underestimate)",
    "uni": "单一(unique, uniform)",
}

SUFFIXES = {
    "able": "可…的/能…的(readable, movable)",
    "age": "状态/集合(shortage, usage)",
    "al": "…的(natural, personal)",
    "ance": "状态/性质(importance, appearance)",
    "ant": "…的人/…的(assistant, important)",
    "ary": "…的/场所(necessary, library)",
    "ate": "使…/…的(create, accurate)",
    "ation": "动作/状态(education, information)",
    "ed": "已…的/被…的(interested, excited)",
    "ence": "状态/性质(difference, existence)",
    "ent": "…的/…的人(different, student)",
    "er": "…的人/比较级(teacher, bigger)",
    "est": "最…(biggest, smallest)",
    "ful": "充满…的(beautiful, powerful)",
    "fy": "使…化(simplify, classify)",
    "ial": "…的(industrial, commercial)",
    "ian": "…的人/…的(musician, Canadian)",
    "ible": "可…的(possible, visible)",
    "ic": "…的(scientific, atomic)",
    "ical": "…的(political, historical)",
    "ify": "使…(beautify, simplify)",
    "ing": "正在…/…的(interesting, running)",
    "ion": "动作/状态(action, decision)",
    "ish": "…的/像…(childish, reddish)",
    "ism": "主义/学说(socialism, realism)",
    "ist": "…家/…者(scientist, artist)",
    "ity": "性质/状态(reality, ability)",
    "ive": "有…倾向的(active, creative)",
    "ize": "使…化(modernize, realize)",
    "less": "无…的/不…的(hopeless, careless)",
    "logy": "…学/论(biology, technology)",
    "ly": "…地(quickly, carefully)",
    "ment": "行为/状态/物(development, equipment)",
    "ness": "性质/状态(happiness, darkness)",
    "or": "…者/…器(actor, calculator)",
    "ory": "…的/场所(factory, laboratory)",
    "ous": "有…性质的(famous, dangerous)",
    "ship": "关系/状态(friendship, leadership)",
    "sion": "动作/状态(decision, discussion)",
    "tion": "动作/状态(attention, solution)",
    "ture": "动作/结果(mixture, culture)",
    "ty": "性质/状态(safety, beauty)",
    "ward": "向…方向(forward, backward)",
}

ROOTS = {
    "act": "行动/做(action, react)",
    "ag": "做/驱动(agent, agenda)",
    "am": "爱(amateur, amiable)",
    "anim": "生命/精神(animal, animate)",
    "ann": "年(annual, anniversary)",
    "aqua": "水(aquarium, aquatic)",
    "arch": "统治/首领(monarch, architect)",
    "aud": "听(audience, audio)",
    "bell": "战斗(rebel, bellicose)",
    "bio": "生命(biology, biography)",
    "cap": "头/拿(captain, capital)",
    "ced": "走/让步(precede, concede)",
    "cept": "拿/取(accept, concept)",
    "cid": "切/杀(decide, suicide)",
    "circ": "圆/环(circle, circus)",
    "claim": "喊/叫(claim, exclaim)",
    "clar": "清楚(clear, clarify)",
    "clud": "关闭(include, conclude)",
    "cogn": "知道(cognitive, recognize)",
    "corp": "身体(corporation, corpse)",
    "cred": "相信(credit, incredible)",
    "cur": "跑/流动(current, occur)",
    "cycl": "圆/环(cycle, bicycle)",
    "dict": "说(predict, dictionary)",
    "don": "给予(donate, pardon)",
    "duc": "引导(produce, introduce)",
    "dur": "持续(durable, during)",
    "equ": "相等(equal, equation)",
    "fac": "做/制造(factory, manufacture)",
    "fer": "带来/承受(transfer, suffer)",
    "fid": "信任(confident, fidelity)",
    "fin": "结束/边界(finish, define)",
    "flect": "弯曲(reflect, flexible)",
    "flu": "流动(fluent, influence)",
    "form": "形状(form, transform)",
    "gen": "产生/种族(generate, gene)",
    "geo": "地球/土地(geography, geology)",
    "grad": "步/走(grade, gradual)",
    "graph": "写/画(graph, photograph)",
    "her": "黏附(adhere, coherent)",
    "ject": "投/扔(inject, project)",
    "jud": "判断(judge, prejudice)",
    "lect": "选/收集(collect, select)",
    "leg": "法律/读(legal, legible)",
    "lev": "举起/轻(elevate, lever)",
    "loc": "位置(locate, local)",
    "log": "说/思想(dialogue, logic)",
    "lumin": "光(illuminate, luminous)",
    "man": "手(manual, manage)",
    "mand": "命令(command, demand)",
    "mar": "海(marine, submarine)",
    "medi": "中间(medium, medieval)",
    "memor": "记忆(memory, remember)",
    "ment": "头脑/心智(mental, mention)",
    "meter": "测量(thermometer, kilometer)",
    "migr": "迁移(migrate, immigrant)",
    "min": "小/突出(minimum, prominent)",
    "miss": "送/发送(mission, dismiss)",
    "mob": "移动(mobile, automobile)",
    "mot": "移动(motor, promote)",
    "nat": "出生/天生(nature, native)",
    "neg": "否定(negative, neglect)",
    "norm": "规则/标准(normal, enormous)",
    "not": "知道/标记(note, notice)",
    "nov": "新(novel, innovate)",
    "numer": "数字(number, numerous)",
    "oper": "工作(operate, cooperate)",
    "opt": "选择/最好(option, optimal)",
    "ord": "顺序(order, coordinate)",
    "part": "部分/分开(part, participate)",
    "pass": "通过/感觉(passage, passion)",
    "path": "感觉/疾病(sympathy, pathology)",
    "ped": "脚(pedal, expedition)",
    "pel": "推动(compel, repel)",
    "pend": "悬挂/支付(depend, suspend)",
    "pet": "追求/寻求(compete, petition)",
    "phon": "声音(telephone, symphony)",
    "photo": "光(photograph, photon)",
    "plic": "折叠(complicated, duplicate)",
    "pol": "城市/政治(politics, metropolis)",
    "pon": "放置(postpone, component)",
    "port": "携带/门(transport, airport)",
    "pos": "放置(position, compose)",
    "press": "压(compress, express)",
    "prim": "第一(primary, primitive)",
    "psych": "心灵(psychology, psychic)",
    "publ": "公共(public, publish)",
    "put": "思考/计算(compute, dispute)",
    "quer": "寻求(question, require)",
    "rect": "直/正确(correct, direct)",
    "rupt": "断裂(interrupt, erupt)",
    "scend": "爬升(ascend, descend)",
    "sci": "知道(science, conscious)",
    "scrib": "写(describe, prescribe)",
    "secut": "跟随(consecutive, execute)",
    "sens": "感觉(sense, sensitive)",
    "sequ": "跟随(sequence, consequence)",
    "serv": "保持/服务(observe, preserve)",
    "sign": "标记(signal, design)",
    "simil": "相似(similar, simulate)",
    "sist": "站立(consist, resist)",
    "sol": "单独/太阳(solo, solar)",
    "solv": "解开(solve, dissolve)",
    "spec": "看(inspect, spectacle)",
    "spir": "呼吸(inspire, spirit)",
    "st": "站立(stand, stable)",
    "struct": "建造(construct, structure)",
    "sum": "拿/取(assume, consume)",
    "tact": "触碰(contact, tactile)",
    "tain": "拿住(contain, maintain)",
    "tect": "遮盖(detect, protect)",
    "tempor": "时间(temporary, contemporary)",
    "tend": "伸展/趋向(tend, extend)",
    "terr": "土地(territory, terrain)",
    "test": "证明(testify, protest)",
    "therm": "热(thermal, thermometer)",
    "tract": "拉/拖(attract, extract)",
    "trib": "给予(tribute, contribute)",
    "urb": "城市(urban, suburb)",
    "vac": "空(vacuum, vacant)",
    "val": "价值/力量(value, valid)",
    "ven": "来(adventure, convene)",
    "ver": "真实(verify, verdict)",
    "vert": "转(convert, reverse)",
    "vid": "看(video, evident)",
    "viv": "生命/活(vivid, survive)",
    "voc": "声音/呼喊(voice, advocate)",
    "volv": "卷/转(involve, revolve)",
}


def analyze_word_structure(word):
    """Analyze word structure: identify prefix, root, suffix."""
    parts = []
    word_lower = word.lower()

    # Check prefixes (longest match first)
    found_prefix = None
    sorted_prefixes = sorted(PREFIXES.keys(), key=len, reverse=True)
    for prefix in sorted_prefixes:
        if word_lower.startswith(prefix) and len(prefix) >= 2:
            remaining = word_lower[len(prefix):]
            if len(remaining) >= 2:
                found_prefix = prefix
                parts.append(f"前缀: {prefix}({PREFIXES[prefix]})")
                word_lower = remaining
                break

    # Check suffixes
    found_suffix = None
    sorted_suffixes = sorted(SUFFIXES.keys(), key=len, reverse=True)
    for suffix in sorted_suffixes:
        if word_lower.endswith(suffix) and len(suffix) >= 2:
            remaining = word_lower[:-len(suffix)]
            if len(remaining) >= 2:
                found_suffix = suffix
                parts.append(f"后缀: {suffix}({SUFFIXES[suffix]})")
                word_lower = remaining
                break

    # Check root
    found_root = None
    sorted_roots = sorted(ROOTS.keys(), key=len, reverse=True)
    for root in sorted_roots:
        if root in word_lower and len(root) >= 2:
            if len(parts) > 0:
                parts.append(f"词根: {root}({ROOTS[root]})")
            else:
                parts.append(f"词根: {root}({ROOTS[root]})")
            found_root = root
            break

    if not parts:
        return ""
    return " | ".join(parts)


# ══════════════════════════════════════════════════════════════════════
# 核心函数
# ══════════════════════════════════════════════════════════════════════

def read_message():
    raw_len = sys.stdin.buffer.read(4)
    if not raw_len:
        return None
    msg_len = struct.unpack("@I", raw_len)[0]
    raw_msg = sys.stdin.buffer.read(msg_len)
    return json.loads(raw_msg.decode("utf-8"))


def send_message(data):
    payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("@I", len(payload)))
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def query_google_translate(word):
    """Query Google Translate API - same backend as Immersive Translate."""
    try:
        q = urllib.parse.quote(word)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q={q}"
        resp = urllib.request.urlopen(url, timeout=3)
        data = json.loads(resp.read().decode("utf-8"))
        if data and data[0] and data[0][0]:
            return data[0][0][0]
    except Exception:
        pass
    return None


def query_youdao(word):
    """Query Youdao (有道) dictionary - free web API."""
    try:
        q = urllib.parse.quote(word)
        # Youdao dict suggest API
        url = f"https://dict.youdao.com/suggest?num=5&doctype=json&q={q}"
        resp = urllib.request.urlopen(url, timeout=3)
        data = json.loads(resp.read().decode("utf-8"))
        if data and data.get("data") and data["data"].get("entries"):
            for entry in data["data"]["entries"]:
                if entry.get("explain"):
                    return entry["explain"]
        return None
    except Exception:
        pass

    # Fallback: scrape dict page
    try:
        q = urllib.parse.quote(word)
        url = f"https://dict.youdao.com/w/eng/{q}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=3)
        html = resp.read().decode("utf-8", errors="replace")
        match = re.search(r"<li>([^<]*?[一-鿿][^<]*)</li>", html)
        if match:
            return match.group(1).strip()
    except Exception:
        pass
    return None


def detect_obsidian_vault():
    """Auto-detect Obsidian vault in common locations."""
    import glob as glob_mod
    home = os.path.expanduser("~")
    # Common vault locations
    candidates = [
        os.path.join(home, "文档", "Obsidian Vault"),
        os.path.join(home, "Documents", "Obsidian Vault"),
        os.path.join(home, "Obsidian Vault"),
    ]
    # Search for .obsidian directories (limit depth for speed)
    for root, dirs, _ in os.walk(home):
        if ".obsidian" in dirs:
            candidates.append(root)
        # Limit to 2 levels deep
        depth = root.replace(home, "").count(os.sep)
        if depth >= 3:
            dirs.clear()
    for path in candidates:
        if os.path.isdir(path) and os.path.isdir(os.path.join(path, ".obsidian")):
            return path
    return None


def enrich_from_dict(word):
    """Get phonetics, pos, etymology from offline dictionary."""
    entry = FULL_DICT.get(word.lower())
    if entry:
        return entry[0], entry[1], entry[2], entry[3] if len(entry) > 3 else ""
    return "", "", "", ""


def _parse_entries(content):
    """Parse markdown entries from file content. Returns (header, list_of_entry_blocks).
    Handles both old format (- word :: ...) and new format (### word ...)."""
    content = content.rstrip("\n")
    # Split header from body
    if "\n\n" in content:
        parts = content.split("\n\n", 1)
        header = parts[0]
        body = parts[1].strip()
    else:
        header = content
        body = ""

    # Detect format: old uses "- word ::", new uses "### word "
    is_old_format = body.strip().startswith("- ") and " :: " in body

    entries = []
    if is_old_format:
        # Migrate old format lines to new format blocks
        for line in body.split("\n"):
            line = line.strip()
            if not line.startswith("- "):
                continue
            # Parse: "- word :: /pron/ :: [pos] meaning  ← etymology"
            # or:    "- word :: [pos] meaning  ← etymology"
            rest = line[2:]  # remove "- "
            parts = rest.split(" :: ")
            w = parts[0].strip()
            pron = ""
            if len(parts) == 3:
                pron = parts[1].strip()
                pos_meaning = parts[2].strip()
            else:
                pos_meaning = parts[1].strip() if len(parts) > 1 else ""
            ety = ""
            if "  ← " in pos_meaning:
                pos_meaning, ety = pos_meaning.split("  ← ", 1)
            if pron and pron.startswith("/") and pron.endswith("/"):
                entry = f"### {w} {pron}\n[{pos_meaning}]" if not pos_meaning.startswith("[") else f"### {w} {pron}\n{pos_meaning}"
            else:
                if pron:
                    pos_meaning = f"{pron} {pos_meaning}"
                entry = f"### {w}\n{pos_meaning}" if pos_meaning.startswith("[") else f"### {w}\n[{pos_meaning}]"
            if ety:
                entry += f"\n← *{ety}*"
            entries.append(entry)
    else:
        # New format: blocks separated by blank lines
        current = []
        for line in body.split("\n"):
            if line.startswith("### ") and current:
                entries.append("\n".join(current))
                current = [line]
            elif line.strip():
                current.append(line)
        if current:
            entries.append("\n".join(current))

    return header, entries


def _get_active_file(vault_path, base_name, ext):
    """Find the active file (last one with < 100 words). Create new file if needed."""
    # Count entries in base file
    base_path = os.path.join(vault_path, f"{base_name}{ext}")
    entries, _ = _count_entries(base_path)
    if entries < 100:
        return base_path, entries

    # Find or create numbered files
    index = 1
    while True:
        num_path = os.path.join(vault_path, f"{base_name}{index}{ext}")
        if os.path.exists(num_path):
            n, _ = _count_entries(num_path)
            if n < 100:
                return num_path, n
        else:
            return num_path, 0
        index += 1


def _count_entries(filepath):
    """Count entries and return parsed header + entries from a file."""
    if not os.path.exists(filepath):
        return 0, None
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    entries_count = content.count("\n### ")
    if content.startswith("### "):
        entries_count += 1
    return entries_count, content


def _build_entry(word, pronunciation, pos, meaning, etymology):
    """Build a single word entry block."""
    lines = []
    if pronunciation:
        lines.append(f"### {word} {pronunciation}")
    else:
        lines.append(f"### {word}")
    lines.append(f"[{pos}] {meaning}")
    if etymology:
        lines.append(f"← *{etymology}*")
    return "\n".join(lines)


def write_to_obsidian(vault_path, target_file, word, pronunciation, pos, meaning, etymology):
    dir_name = os.path.dirname(os.path.join(vault_path, target_file))
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    base_name, ext = os.path.splitext(target_file)

    # Find the active file (rotate if ≥100 entries)
    filepath, _ = _get_active_file(vault_path, base_name, ext)

    # Read existing content
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()
        header, entries = _parse_entries(raw)
    else:
        header = "# 论文词汇表"
        entries = []

    # Check duplicate
    for entry in entries:
        first_line = entry.split("\n")[0]
        if first_line.startswith(f"### {word} ") or first_line.strip() == f"### {word}":
            return {"status": "exists", "word": word, "pos": pos, "meaning": meaning,
                    "pronunciation": pronunciation, "etymology": etymology}

    # Build new entry and sort
    new_entry = _build_entry(word, pronunciation, pos, meaning, etymology)
    entries.append(new_entry)
    entries.sort(key=lambda s: s.split("\n")[0].lstrip("### ").lower())

    # Write back
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(header + "\n\n")
        f.write("\n\n".join(entries))
        f.write("\n")

    # Determine final path for the response
    full_path = os.path.join(vault_path, target_file)
    written_to = os.path.relpath(filepath, vault_path) if filepath != full_path else target_file

    return {"status": "ok", "word": word, "pos": pos, "meaning": meaning,
            "pronunciation": pronunciation, "etymology": etymology,
            "file": written_to}


def is_valid_input(text):
    """Validate input: allow single words and phrases (letters, spaces, hyphens)."""
    text = text.strip()
    if not text or len(text) < 2:
        return False
    # Allow letters, spaces, hyphens for phrases
    return bool(re.match(r'^[a-zA-Z][a-zA-Z\s\-]{0,79}$', text))


def handle_message(msg):
    action = msg.get("action", "")

    if action == "test":
        vault = detect_obsidian_vault()
        msg_text = "Native host v4.0 (Google + Youdao) is running"
        if vault:
            msg_text += f"\n检测到 Vault: {vault}"
        return {"status": "ok", "message": msg_text}

    word = msg.get("word", "").strip().lower()
    if not is_valid_input(word):
        return {"status": "error", "message": "请输入有效的英文单词或词组"}

    settings = msg.get("settings", {})
    vault_path = settings.get("vault_path", "")
    target_file = settings.get("target_file", "7英语/论文单词.md")

    # Auto-detect vault if not configured
    if not vault_path or not os.path.isdir(vault_path):
        detected = detect_obsidian_vault()
        if detected:
            vault_path = detected
        else:
            return {"status": "error", "message": "未找到 Obsidian Vault，请在插件中手动配置路径"}

    # Enrich from offline dictionary (phonetics, pos, etymology)
    dict_pron, dict_pos, dict_meaning, dict_etym = enrich_from_dict(word)

    # Step 1: Immersive Translate page text (primary - what user already sees)
    page_translation = msg.get("pageTranslation", "")
    meaning = page_translation.strip() if page_translation else ""

    # Step 2: API translation (Google or Youdao based on user setting)
    api_choice = settings.get("dictionary_api", "google")
    if not meaning and api_choice != "offline":
        if api_choice == "youdao":
            meaning = query_youdao(word)
        else:
            meaning = query_google_translate(word)
        # Fallback: try the other API if first choice fails
        if not meaning and api_choice == "youdao":
            meaning = query_google_translate(word)
        elif not meaning and api_choice == "google":
            meaning = query_youdao(word)

    # Step 3: Offline dictionary
    if not meaning:
        meaning = dict_meaning

    # Step 4: Nothing found
    if not meaning:
        etymology = analyze_word_structure(word)
        if etymology:
            return {"status": "error", "message": f"未找到释义\n词根分析: {etymology}"}
        return {"status": "error", "message": "翻译失败，请检查网络后重试"}

    pronunciation = dict_pron
    pos = dict_pos if dict_pos else "n."
    etymology = dict_etym if dict_etym else analyze_word_structure(word)

    return write_to_obsidian(vault_path, target_file, word, pronunciation, pos, meaning, etymology)


def main():
    while True:
        try:
            msg = read_message()
            if msg is None:
                break
            response = handle_message(msg)
            send_message(response)
        except json.JSONDecodeError:
            break
        except BrokenPipeError:
            break
        except Exception as e:
            try:
                send_message({"status": "error", "message": str(e)})
            except Exception:
                break


if __name__ == "__main__":
    main()
