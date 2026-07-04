import React, { useEffect, useState } from 'react'
import { ArrowRightOutlined, RiseOutlined } from '@ant-design/icons'
import { Button, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'
import { logApi } from '@/api'
import type { NiukeRecord, StatsData } from '@/api/types'
import { companyBrands } from '@/constants/companies'
import { formatDisplayTime } from '@/utils/datetime'

const { Paragraph, Text, Title } = Typography

const marketSignals = [
  {
    index: '01',
    label: 'AI Engineering',
    title: 'AI 正在成为工程岗位的通用能力',
    text: '从 Agent、RAG 到智能化研发工具，大模型能力正在进入后端、客户端与基础架构岗位。',
    trend: '持续升温',
  },
  {
    index: '02',
    label: 'Infrastructure',
    title: '基础架构仍然决定工程上限',
    text: '分布式系统、性能、稳定性和云原生，依然是大厂技术岗位反复强调的底层能力。',
    trend: '长期高频',
  },
  {
    index: '03',
    label: 'Real Experience',
    title: '项目深度，比技术名词更重要',
    text: '岗位和面试都在关注真实规模、方案取舍、效果指标，以及你到底解决了什么问题。',
    trend: '核心信号',
  },
]

const capabilityLinks = [
  {
    skill: 'Redis 与缓存',
    requirement: '高并发服务、缓存架构、稳定性治理',
    questions: ['缓存击穿怎么处理？', '分布式锁为什么选 Redisson？'],
    post: '后端开发',
  },
  {
    skill: '大模型应用',
    requirement: 'Agent、RAG、模型评估与工程落地',
    questions: ['RAG 链路怎么设计？', '召回效果如何评估？'],
    post: '人工智能/算法',
  },
  {
    skill: '前端工程化',
    requirement: '性能优化、跨端架构与复杂业务交付',
    questions: ['首屏性能怎么优化？', '组件体系如何设计？'],
    post: '前端开发',
  },
]

const PublicHome: React.FC = () => {
  const navigate = useNavigate()
  const [stats, setStats] = useState<StatsData | null>(null)
  const [featured, setFeatured] = useState<NiukeRecord[]>([])

  useEffect(() => {
    logApi.stats().then(setStats).catch(() => setStats(null))
    logApi.records({ limit: 20, offset: 0 })
      .then((data) => {
        const selected = (data?.data || [])
          .filter((item) => item.company && item.company !== '未知公司' && item.content?.length > 80)
          .slice(0, 3)
        setFeatured(selected)
      })
      .catch(() => setFeatured([]))
  }, [])

  const topPosts = [...(stats?.post_stats || [])].sort((a, b) => b.count - a.count).slice(0, 6)

  return (
    <div className="public-page premium-home">
      <header className="public-nav premium-nav">
        <button className="public-brand" onClick={() => navigate('/')}>
          <img src="/offerlens.svg" alt="OfferLens" />
          <strong>OfferLens</strong>
        </button>
        <nav>
          <Button type="text" onClick={() => navigate('/interviews')}>面经库</Button>
          <Button type="text" onClick={() => navigate('/jobs')}>职位雷达</Button>
          <Button type="text" onClick={() => navigate('/ai-analysis')}>AI 分析</Button>
          <Button type="text" onClick={() => navigate('/admin')}>后台入口</Button>
          <Button type="primary" onClick={() => navigate('/interviews')}>立即开始</Button>
        </nav>
      </header>

      <main>
        <div className="premium-above-fold">
          <section className="premium-hero">
            <Text className="premium-eyebrow">Interview intelligence, built from reality.</Text>
            <Title>看清面试。<br />看见机会。</Title>
            <Paragraph>
              从 {stats?.total_records?.toLocaleString() || '8,000+'} 篇真实面经，到大厂招聘官网岗位。
              <br />知道市场需要什么，也知道下一场面试该准备什么。
            </Paragraph>
            <div className="premium-hero-actions">
              <Button type="primary" size="large" onClick={() => navigate('/interviews')}>
                浏览真实面经 <ArrowRightOutlined />
              </Button>
              <Button size="large" onClick={() => navigate('/jobs')}>
                探索官网职位
              </Button>
            </div>
          </section>

          <section className="premium-data-strip">
            <div><strong>{stats?.total_records?.toLocaleString() || '-'}</strong><span>真实面经</span></div>
            <div><strong>{topPosts.length || '-'}</strong><span>热门方向</span></div>
            <div><strong>8</strong><span>招聘官网数据源</span></div>
            <div><strong>24h</strong><span>持续更新情报</span></div>
          </section>

          <section className="brand-ribbon-section">
            <Text>面经覆盖热门公司</Text>
            <div className="brand-ribbon">
              <div>
                {[...companyBrands, ...companyBrands].map((company, index) => (
                  <button
                    key={`${company.name}-${index}`}
                    onClick={() => navigate(`/interviews?company=${encodeURIComponent(company.searchName || company.name)}`)}
                    aria-label={`查看 ${company.name} 面经`}
                  >
                    <img src={company.logo} alt={`${company.name} logo`} />
                  </button>
                ))}
              </div>
            </div>
          </section>
        </div>

        <section className="premium-section">
          <div className="premium-section-heading">
            <Text>Market Signals</Text>
            <Title level={2}>本周市场信号</Title>
            <Paragraph>从岗位要求里，读懂大厂正在把筹码放在哪里。</Paragraph>
          </div>
          <div className="signal-list">
            {marketSignals.map((signal) => (
              <article key={signal.index}>
                <span className="signal-index">{signal.index}</span>
                <div>
                  <Text>{signal.label}</Text>
                  <h3>{signal.title}</h3>
                  <p>{signal.text}</p>
                </div>
                <b><RiseOutlined /> {signal.trend}</b>
              </article>
            ))}
          </div>
          <Button type="link" className="section-link" onClick={() => navigate('/jobs')}>
            查看真实官网岗位 <ArrowRightOutlined />
          </Button>
        </section>

        <section className="premium-section capability-section">
          <div className="premium-section-heading">
            <Text>Requirements × Interviews</Text>
            <Title level={2}>岗位写要求。面试验能力。</Title>
            <Paragraph>把招聘需求和真实面试问题放在一起，复习重点就不再靠猜。</Paragraph>
          </div>
          <div className="capability-grid">
            {capabilityLinks.map((item) => (
              <button key={item.skill} onClick={() => navigate(`/interviews?post=${encodeURIComponent(item.post)}`)}>
                <span>{item.skill}</span>
                <h3>{item.requirement}</h3>
                <div>
                  {item.questions.map((question) => <p key={question}>{question}</p>)}
                </div>
                <b>查看相关面经 <ArrowRightOutlined /></b>
              </button>
            ))}
          </div>
        </section>

        <section className="premium-section direction-section">
          <div className="premium-section-heading inline">
            <div>
              <Text>Popular Tracks</Text>
              <Title level={2}>热门岗位方向</Title>
            </div>
            <Button type="link" onClick={() => navigate('/interviews')}>查看全部面经 <ArrowRightOutlined /></Button>
          </div>
          <div className="direction-ranking">
            {(topPosts.length ? topPosts : [
              { post: '后端开发', count: 4643 },
              { post: '前端开发', count: 1553 },
              { post: '人工智能/算法', count: 426 },
            ]).map((item, index) => (
              <button key={item.post} onClick={() => navigate(`/interviews?post=${encodeURIComponent(item.post)}`)}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                <h3>{item.post}</h3>
                <div><i style={{ width: `${Math.max(18, 100 - index * 13)}%` }} /></div>
                <b>{item.count.toLocaleString()} 篇</b>
              </button>
            ))}
          </div>
        </section>

        <section className="premium-section featured-section">
          <div className="premium-section-heading">
            <Text>Selected Interviews</Text>
            <Title level={2}>值得先看的面经</Title>
            <Paragraph>少一点漫无目的，多一点高质量输入。</Paragraph>
          </div>
          <div className="featured-interviews">
            {(featured.length ? featured : [
              { id: 0, company: '字节跳动', post: '后端开发', title: '后端二面高频问题复盘', content: 'Java、并发、Redis 与项目追问。', edit_time: null },
            ] as NiukeRecord[]).map((record) => (
              <button key={record.id} onClick={() => navigate(`/interviews?company=${encodeURIComponent(record.company)}&post=${encodeURIComponent(record.post)}`)}>
                <div><span>{record.company || '大厂面经'}</span><span>{record.post}</span></div>
                <h3>{record.title}</h3>
                <p>{record.content || '查看真实面试问题与复习重点。'}</p>
                <footer>
                  <small>{formatDisplayTime(record.edit_time)}</small>
                  <b>阅读面经 <ArrowRightOutlined /></b>
                </footer>
              </button>
            ))}
          </div>
        </section>

        <section className="premium-cta">
          <Text>OfferLens</Text>
          <Title level={2}>下一场面试，从看清开始。</Title>
          <div>
            <Button type="primary" size="large" onClick={() => navigate('/interviews')}>开始准备</Button>
            <Button size="large" onClick={() => navigate('/jobs')}>探索职位</Button>
          </div>
        </section>
      </main>

      <footer className="premium-footer">
        <span>OfferLens · 面试与职业情报</span>
        <span>真实面经 · 官网岗位 · 结构化复习</span>
      </footer>
    </div>
  )
}

export default PublicHome
