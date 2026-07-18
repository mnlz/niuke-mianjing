import React from 'react'
import { Button } from 'antd'
import { ArrowRightOutlined, PrinterOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import AnalysisHeader from './AnalysisHeader'
import './style.css'

const navItems = [
  ['must-read', '本场必看'], ['frequency', '近期高频题'], ['projects', '项目拷打'], ['fundamentals', '简历八股'],
  ['algorithms', '算法预测'], ['resume', '简历修改'], ['appendix', '附录'],
]

const coreQuestions = [
  ['P0', '项目', '统一大模型执行层如何屏蔽模型差异，并处理超时、取消与 SSE 中断？', 'JD 要求 AI 应用落地；简历直接写到多模型、SSE；近期 7/12 篇出现 AI 工程问题。', '【JD-01】【简历】【面经-08】【面经-09】【面经-12】'],
  ['P0', '项目', '订单支付、异步交付和掉单补偿怎样保证幂等与最终一致？', '岗位属于国际支付；简历写到完整交易链路；近期面经高频追问异常分支。', '【JD-01】【简历】【面经-01】【面经-10】'],
  ['P0', '项目', '为什么使用 Redis + Canal 同步 Elasticsearch？任一环节失败会怎样？', '简历同时暴露缓存、搜索与数据同步，面试官会沿一致性连续追问。', '【简历】【面经-01】【面经-10】'],
  ['P0', '八股', 'SSE 和 WebSocket 的差异是什么？客户端断开后服务端资源如何释放？', '简历中的 ResponseBodyEmitter 会直接触发；近期面经 #699 原题出现。', '【简历】【面经-09】'],
  ['P0', '八股', '缓存与数据库如何保证一致性？延迟双删的第二次删什么窗口？', '近期 #418、#704 直接出现，且命中简历 Redis 使用场景。', '【简历】【面经-01】【面经-10】'],
  ['P0', '算法', '编辑距离', '近期字节后端一面 #704 原题，动态规划是当前样本的明确考点。', '【面经-10】'],
  ['P1', '算法', '二叉树最大路径和', '近期抖音小程序一面 #611 原题，树题也在三轮 OC 面经中连续出现。', '【面经-03】【面经-06】'],
  ['P1', '八股', 'CompletableFuture 使用哪个线程池？如何避免某个模型拖垮整个请求？', '简历写到多模型异步调用，岗位强调高并发和稳定性。', '【JD-01】【简历】【AI推断】'],
]

const frequencyRows = [
  ['12 / 12', '简历与项目深挖', '#418 #433 #477 #609 #610 #611 #653 #694 #699 #704 #695 #706', '从个人贡献继续追到选型、规模、异常分支和底层原理'],
  ['11 / 12', '现场算法 / 编码', '#418 #433 #477 #609 #611 #653 #694 #699 #704 #695 #706', '多数以现场手撕收尾，包含 ACM 完整输入输出'],
  ['8 / 12', '数据库、缓存与消息系统', '#418 #611 #653 #694 #699 #704 #695 #706', 'MySQL 索引、Redis、一致性、MQ 幂等都从项目落到原理'],
  ['7 / 12', 'AI / RAG / AI Coding', '#609 #610 #694 #699 #704 #695 #706', '不止问模型调用，还问评估、Token、KV Cache、监控与成本'],
]

const algorithms = [
  ['P0', '编辑距离', '#704 · 2026-06-21', '近期字节后端一面原题'],
  ['P0', '最长上升子序列', '#699 · 2026-06-22', '近期字节 AI 项目面原题'],
  ['P0', '三数之和', '#706 · 2026-06-20', '字节云项目深挖后原题'],
  ['P1', '二叉树最大路径和', '#611 · 2026-06-26', '抖音小程序一面原题'],
  ['P1', '旋转排序数组中查找目标值（LeetCode 81）', '#477 · 2026-07-03', '三轮技术面二面原题'],
  ['P1', '切割回文子串', '#418 · 2026-07-07', '当前样本中日期最近的字节后端原题'],
  ['P1', '中序遍历下一节点（JZ8）', '#477 · 2026-07-03', '三轮技术面一面原题'],
  ['P2', '链表倒数第 K 个节点（JZ22）', '#477 · 2026-07-03', '三轮技术面三面原题'],
]

const SampleReportPage: React.FC = () => {
  const navigate = useNavigate()

  return (
    <div className="ai-product-page ai-reports-page">
      <AnalysisHeader active="sample" />
      <main>
        <div className="ai-reports-title ai-sample-title">
          <div><span>PUBLIC SAMPLE · INTERVIEW HANDBOOK</span><h1>AI 报告示例</h1><p>一份可以直接拿去准备面试的核心资料，而不是另一张泛化评分表。</p></div>
          <div className="ai-sample-tools"><Button icon={<PrinterOutlined />} onClick={() => window.print()}>打印 / 下载 PDF</Button><Button type="primary" onClick={() => navigate('/ai-analysis/create?report=full')}>生成我的报告 <ArrowRightOutlined /></Button></div>
        </div>

        <div className="ai-handbook-shell">
          <aside className="ai-handbook-toc">
            <small>目录</small>
            {navItems.map(([id, label], index) => <a key={id} href={`#${id}`}><i>{String(index).padStart(2, '0')}</i>{label}</a>)}
            <p>按“岗位重要性 × 近期频率 × 简历触发”排序</p>
          </aside>

          <article className="ai-handbook-paper">
            <header className="ai-handbook-cover">
              <small>RPT-SAMPLE-0713 · ANONYMIZED</small>
              <h2>字节跳动｜AI 应用后端<br />面试核心资料</h2>
              <p>精确岗位：AI应用后端开发（支付网络&资金业务）-国际支付</p>
              <div><span>1 个精确 JD</span><span>12 篇近期面经</span><span>1 份匿名简历</span><span>更新于 2026-07-13</span></div>
              <blockquote>读完后，你应该能明确回答四件事：项目会被怎样拷打、八股如何从简历触发、最近算法原题有哪些、简历该怎样改。</blockquote>
            </header>

            <section id="must-read" className="ai-handbook-section">
              <div className="ai-handbook-section-title"><i>00</i><div><small>READ FIRST</small><h3>本场必看</h3><p>正文最高优先级问题，先把这些练到能连续回答。</p></div></div>
              <div className="ai-handbook-core-list">
                {coreQuestions.map(([priority, type, question, reason, references], index) => <article key={question}><b>{String(index + 1).padStart(2, '0')}</b><div><span className={`priority ${priority.toLowerCase()}`}>{priority}</span><em>{type}</em><h4>{question}</h4><p>{reason}{references}</p></div></article>)}
              </div>
            </section>

            <section id="frequency" className="ai-handbook-section">
              <div className="ai-handbook-section-title"><i>01</i><div><small>OBSERVED DATA</small><h3>近期高频题</h3><p>样本：12 篇字节后端面经，2026-06-20 至 2026-07-07。这里只统计样本中直接出现的内容。</p></div></div>
              <div className="ai-handbook-frequency">
                {frequencyRows.map(([count, topic, refs, detail]) => <article key={topic}><strong>{count}</strong><div><h4>{topic}</h4><p>{detail}</p><small>{refs}</small></div></article>)}
              </div>
              <div className="ai-handbook-note"><b>怎么理解：</b>“12/12”是这 12 篇样本中的观察值，不是下一场面试的出现概率；由 JD 或简历推断的问题不混入频率。</div>
            </section>

            <section id="projects" className="ai-handbook-section">
              <div className="ai-handbook-section-title"><i>02</i><div><small>INTERVIEWER VIEW</small><h3>项目拷打地图</h3><p>从面试官角度拆开每个项目，答案按 30 秒、完整回答、连续追问和事实边界分层。</p></div></div>

              <article className="ai-handbook-project">
                <header><div><small>PROJECT 01 · P0</small><h4>统一 OpenAI 应用服务</h4></div><span>模型适配</span><span>SSE</span><span>异步并发</span><span>稳定性</span></header>
                <h5>核心拷打：为什么需要工厂 + 策略？它解决了什么真实变化？</h5>
                <dl>
                  <dt>30 秒回答</dt><dd>统一层隔离的是不同模型供应商在鉴权、请求参数和响应结构上的差异。工厂负责按模型配置创建执行器，策略负责封装各模型调用行为，让业务层只依赖统一接口；是否值得使用，取决于项目里是否真的存在多模型切换与并行调用。【简历】</dd>
                  <dt>完整回答</dt><dd>先讲变化源：模型供应商和调用协议；再画出业务层 → 统一接口 → 具体模型策略的调用链；最后说明新增模型时改哪里、公共超时和日志放哪里。不要只回答“为了低耦合”，要用一次真实扩展说明设计价值。【简历】【AI推断】</dd>
                  <dt>连续追问</dt><dd>为什么不是简单 if/else？工厂和策略各自边界是什么？供应商返回流式与非流式响应如何统一？某个模型失败是否影响其他模型？</dd>
                  <dt>事实边界</dt><dd>【需本人替换：实际接入模型数量、一次新增模型的改动、超时/重试方案、本人负责范围】</dd>
                </dl>
                <h5>核心拷打：SSE 连接断开后，服务端任务和线程怎么处理？</h5>
                <dl>
                  <dt>30 秒回答</dt><dd>SSE 适合服务端持续向浏览器单向推送。连接断开时不能只等写入报错，需要在完成、超时和异常回调中释放 ResponseBodyEmitter，并取消仍在运行的模型任务，避免线程和连接继续占用。【简历】【面经-09】</dd>
                  <dt>完整回答</dt><dd>按“为什么选 SSE → 连接生命周期 → 任务取消 → 背压与超时 → 观测指标”展开，并明确当前项目已经实现的部分和待补部分。</dd>
                  <dt>连续追问</dt><dd>SSE 与 WebSocket 怎么选？代理层会不会缓冲？多模型结果并发写回是否线程安全？慢客户端如何处理？</dd>
                  <dt>事实边界</dt><dd>【需本人替换：当前超时时间、是否实现取消、线程池配置、异常回调和线上指标】</dd>
                </dl>
              </article>

              <article className="ai-handbook-project">
                <header><div><small>PROJECT 02 · P0</small><h4>集成电路创新成果交易平台</h4></div><span>支付</span><span>RabbitMQ</span><span>Redis</span><span>Canal + ES</span></header>
                <h5>核心拷打：支付回调与异步交付怎样避免重复执行？</h5>
                <dl>
                  <dt>30 秒回答</dt><dd>先以订单状态机和业务唯一键兜住重复回调，再让消费端按订单/事件 ID 做幂等；消息确认、重试和补偿只能保证“至少一次”，最终要靠业务幂等避免重复交付。【简历】【JD-01】</dd>
                  <dt>完整回答</dt><dd>按“支付回调验签 → 条件更新订单状态 → 写入交付事件 → MQ 消费 → 失败重试/补偿 → 对账”说明。数据库事务、消息发送与业务交付不在同一原子边界时，必须主动指出失败窗口。</dd>
                  <dt>连续追问</dt><dd>两台 Pod 同时消费同一消息怎么办？锁过期但业务没结束怎么办？消息发送成功、事务回滚怎么办？补偿任务如何避免再次重复？</dd>
                  <dt>事实边界</dt><dd>【需本人替换：真实状态字段、唯一约束、消息确认模式、重试次数、对账/补偿实现】</dd>
                </dl>
                <h5>核心拷打：MySQL、Redis、Elasticsearch 三份数据不一致怎么办？</h5>
                <dl>
                  <dt>30 秒回答</dt><dd>先声明 MySQL 是事实源，Redis 和 Elasticsearch 都允许最终一致；写请求优先落库，再通过删除缓存和 Canal 增量同步派生数据，同时准备失败重放和定期校验。【简历】</dd>
                  <dt>完整回答</dt><dd>分别说明缓存和搜索索引的一致性目标、可接受延迟、失败窗口与修复手段。不要把 Canal 说成强一致，它只是捕获 binlog 变化，消费失败、乱序和全量重建仍需处理。</dd>
                  <dt>连续追问</dt><dd>为什么更新缓存而不是删除？Canal 事件乱序怎么办？ES 写入失败如何重放？缓存击穿时如何保护数据库？</dd>
                  <dt>事实边界</dt><dd>【需本人替换：项目真实更新顺序、Canal 消费方式、失败重试、数据校验与恢复流程】</dd>
                </dl>
              </article>
            </section>

            <section id="fundamentals" className="ai-handbook-section">
              <div className="ai-handbook-section-title"><i>03</i><div><small>RESUME-TRIGGERED</small><h3>简历触发八股</h3><p>不是通用题库；每组都把经典问法落回你的项目。</p></div></div>
              <div className="ai-handbook-fundamentals">
                <article><span>P0 · 网络</span><h4>经典：SSE 和 WebSocket 有什么区别？</h4><p><b>经典答案：</b>SSE 基于 HTTP 长连接、服务端单向推送、文本事件且浏览器原生支持重连；WebSocket 建立升级后的全双工通道，更适合高频双向通信。</p><h4>项目问法：为什么模型流式输出选 SSE？断线如何停止生成？</h4><p><b>项目回答：</b>当前业务主要是服务端向页面持续推 token，SSE 更简单；回答必须继续覆盖取消、超时、代理缓冲与资源释放。【简历】【面经-09】</p></article>
                <article><span>P0 · 并发</span><h4>经典：CompletableFuture 默认使用什么线程池？</h4><p><b>经典答案：</b>未显式指定时异步方法通常进入 ForkJoinPool.commonPool；阻塞 I/O 混用公共池可能造成饥饿，应按任务性质使用独立、有界线程池并处理超时。</p><h4>项目问法：并发调用多个模型时，一个长尾请求会怎样？</h4><p><b>项目回答：</b>为模型调用使用隔离线程池和独立超时，汇总时定义部分成功策略；客户端断开后传播取消信号。【简历】【JD-01】</p></article>
                <article><span>P0 · 数据一致性</span><h4>经典：缓存和数据库如何保持一致？</h4><p><b>经典答案：</b>先明确强一致还是最终一致；常见旁路缓存是先更新数据库再删除缓存，并用重试/消息兜底删除失败，仍需解释并发读写窗口。</p><h4>项目问法：商品更新后 Redis 与 ES 分别何时可见？</h4><p><b>项目回答：</b>MySQL 为事实源，缓存删除和 Canal 同步分别有独立失败窗口；回答需给出项目真实恢复手段。【简历】【面经-01】【面经-10】</p></article>
                <article><span>P1 · MySQL</span><h4>经典：联合索引为什么受最左前缀约束？</h4><p><b>经典答案：</b>B+ 树按联合键从左到右排序，缺少前导列时无法直接缩小连续有序区间；是否使用索引仍由优化器结合选择性和成本判断。</p><h4>项目问法：订单查询按用户、状态、时间如何设计索引？</h4><p><b>项目回答：</b>从真实查询条件、等值/范围顺序、排序与回表成本出发，用 EXPLAIN 和数据分布验证，而不是背固定字段顺序。【简历】【面经-10】</p></article>
              </div>
            </section>

            <section id="algorithms" className="ai-handbook-section">
              <div className="ai-handbook-section-title"><i>04</i><div><small>RECENT EXACT QUESTIONS</small><h3>最可能的算法题</h3><p>只展示近期原题与来源；本报告不提供题解、代码和练习验收。</p></div></div>
              <div className="ai-handbook-algorithms">
                {algorithms.map(([priority, name, source, reason], index) => <article key={name}><b>{String(index + 1).padStart(2, '0')}</b><span className={`priority ${priority.toLowerCase()}`}>{priority}</span><div><h4>{name}</h4><p>{reason}</p></div><small>{source}</small></article>)}
              </div>
            </section>

            <section id="resume" className="ai-handbook-section">
              <div className="ai-handbook-section-title"><i>05</i><div><small>BEFORE / AFTER</small><h3>简历修改建议</h3><p>推荐写法保留事实边界；方括号内容必须由本人补齐。</p></div></div>
              <div className="ai-handbook-resume-diff">
                <article><header><span>原始写法</span><span>推荐写法</span></header><div><p>采用 Session 会话模型，通过工厂模式和策略模式设计独立的 OpenAI-SDK，统一对接和管理各类大模型。</p><p>设计统一大模型执行层，隔离供应商鉴权、请求与响应差异；支持 SSE 流式响应及多模型并行调用，并通过【需本人替换：超时/失败隔离机制】控制单模型异常影响。</p></div><footer><b>SCQA：</b>从“用了什么模式”改为“模型差异造成什么问题 → 如何解决 → 带来什么结果”。需补：模型数量、本人职责、真实异常策略。<br /><b>新增追问：</b>为什么不是 if/else？线程池如何配置？断线如何取消？</footer></article>
                <article><header><span>原始写法</span><span>推荐写法</span></header><div><p>实现商品、订单、支付、异步发货、库存扣减、掉单补偿与缓存更新模型。</p><p>负责【需本人替换：具体模块】，串联下单、支付回调与异步交付；通过【需本人替换：唯一约束/状态机/幂等键】避免重复处理，并以【需本人替换：对账或补偿机制】恢复异常订单。</p></div><footer><b>STAR/CAR：</b>把功能清单改为场景、职责、关键动作和可核对结果。需补：真实负责边界、故障窗口、数据量。<br /><b>新增追问：</b>事务与发消息如何一致？补偿会不会重复？库存超卖怎么处理？</footer></article>
                <article><header><span>原始写法</span><span>推荐写法</span></header><div><p>使用 Elasticsearch 实现高效检索，并通过 Canal 保证与 MySQL 数据一致性。</p><p>以 MySQL 为事实源，使用 Canal 订阅 binlog 并增量更新 Elasticsearch，将搜索索引收敛到最终一致；通过【需本人替换：失败重试/重建/校验方式】处理同步失败。</p></div><footer><b>SCQA：</b>删除“保证一致性”的过度承诺，明确一致性等级和修复路径。需补：延迟、乱序和失败恢复。<br /><b>新增追问：</b>Canal 丢消息怎么办？全量重建期间如何服务？</footer></article>
              </div>
            </section>

            <section id="appendix" className="ai-handbook-section">
              <div className="ai-handbook-section-title"><i>06</i><div><small>APPENDIX</small><h3>附录：次优先级追问</h3><p>正文未展开，但面试前仍应逐项确认事实。</p></div></div>
              <div className="ai-handbook-appendix"><article><h4>OpenAI 应用服务</h4><ul><li>P1：Session 的生命周期、隔离范围和过期策略是什么？</li><li>P1：内容审核放在流式输出前还是过程中？误杀与漏放如何处理？</li><li>P2：多模型输出如何比较质量、延迟和成本？</li></ul></article><article><h4>交易平台</h4><ul><li>P1：access token / refresh token 如何轮换与失效？</li><li>P1：RabbitMQ 重复、乱序、积压分别怎样处理？</li><li>P2：MinIO 上传的鉴权、分片和垃圾文件如何处理？</li></ul></article><article><h4>补充八股</h4><ul><li>P1：Redis 分布式锁的续期、可重入与 fencing token。</li><li>P1：JVM OOM 的定位链路与常见泄漏来源。</li><li>P2：MySQL MVCC、隔离级别与幻读。</li></ul></article></div>
              <div className="ai-handbook-boundary"><h4>数据边界</h4><p>岗位：1 个当前官方精确 JD。面经：12 篇，2026-06-20 至 2026-07-07。简历：1 份匿名化 PDF 的解析文本。标为【AI推断】的内容用于补足可能的追问，不代表真实面试题；所有个人贡献、数字和实现必须由候选人确认。</p></div>
            </section>
          </article>
        </div>
      </main>
    </div>
  )
}

export default SampleReportPage
