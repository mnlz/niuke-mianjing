import React, { useEffect, useState } from 'react'
import { ArrowRightOutlined, RobotOutlined } from '@ant-design/icons'
import { Button, Typography } from 'antd'
import { useNavigate } from 'react-router-dom'
import { logApi, recruitmentApi } from '@/api'
import type { NiukeRecord, StatsData } from '@/api/types'
import { companyBrands } from '@/constants/companies'
import { formatDisplayTime } from '@/utils/datetime'
import { buildMarketSignals, featuredInterviewCompanies, pickFeaturedInterviews, type JobMarketSnapshot } from './homeUtils'
import UserSessionButton from '@/components/UserSessionButton'

const { Paragraph, Text, Title } = Typography

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
  const [jobSnapshot, setJobSnapshot] = useState<JobMarketSnapshot | null>(null)

  useEffect(() => {
    logApi.stats().then(setStats).catch(() => setStats(null))
    recruitmentApi.sources().then(async (sources) => {
      const tencent = (sources || []).find((item) => item.source === 'tencent')
      const page = await recruitmentApi.jobs({ source: 'tencent', recruitment_type: 'campus', ai_hot: true, page: 1, page_size: 1 })
      setJobSnapshot({
        sourceCount: sources?.length || 0,
        aiCompanyCount: (sources || []).filter((item) => ['deepseek', 'kimi', 'minimax', 'zhipu'].includes(item.source)).length,
        company: tencent?.company || '腾讯',
        recruitmentType: '校招',
        totalJobs: page?.facet_total || page?.total || 0,
        aiJobs: page?.total || 0,
        engineeringJobs: page?.role_groups?.find((item) => item.id === 'engineering')?.count || 0,
      })
    }).catch(() => setJobSnapshot(null))
    Promise.all(
      featuredInterviewCompanies.map((company) => logApi.records({ company, limit: 6, offset: 0 }).then((data) => data?.data || [])),
    )
      .then((groups) => setFeatured(pickFeaturedInterviews(groups)))
      .catch(() => setFeatured([]))
  }, [])

  const topPosts = [...(stats?.post_stats || [])].sort((a, b) => b.count - a.count).slice(0, 6)
  const marketSignals = buildMarketSignals(jobSnapshot, stats)

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
          <UserSessionButton />
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
              <Button className="premium-ai-button" type="primary" size="large" icon={<RobotOutlined />} onClick={() => navigate('/ai-analysis')}>
                AI 智能分析
              </Button>
              <Button size="large" onClick={() => navigate('/jobs')}>
                大厂热门岗位
              </Button>
            </div>
          </section>

          <section className="premium-data-strip">
            <div><strong>{stats?.total_records?.toLocaleString() || '-'}</strong><span>真实面经</span></div>
            <div><strong>{topPosts.length || '-'}</strong><span>热门方向</span></div>
            <div><strong>{jobSnapshot?.sourceCount || '-'}</strong><span>招聘官网数据源</span></div>
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

        <section className="premium-section market-opportunity-section">
          <div className="premium-section-heading">
            <Text>Live Opportunity Radar</Text>
            <Title level={2}>别再盲投。先看哪些机会值得冲。</Title>
            <Paragraph>从官网岗位判断机会，从真实面经判断难度，再让 AI 把两者变成你的准备清单。</Paragraph>
          </div>
          <div className="market-signal-grid">
            {marketSignals.map((signal) => (
              <button key={signal.index} className={`market-signal-card ${signal.tone}`} onClick={() => navigate(signal.path)}>
                <div className="market-signal-meta"><span>{signal.index}</span><b>{signal.label}</b></div>
                <div className="market-signal-metric"><strong>{signal.metric}</strong><span>{signal.unit}</span></div>
                <h3>{signal.title}</h3>
                <p>{signal.text}</p>
                <footer>{signal.action} <ArrowRightOutlined /></footer>
              </button>
            ))}
          </div>
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
            <Title level={2}>大厂面经精选</Title>
            <Paragraph>优先展示字节、腾讯、阿里的真实面经，先看主流大厂怎么问。</Paragraph>
          </div>
          <div className="featured-interviews">
            {(featured.length ? featured : [
              { id: 0, company: '字节跳动', post: '后端开发', title: '后端二面高频问题复盘', content: 'Java、并发、Redis 与项目追问。', edit_time: null },
              { id: 1, company: '腾讯', post: '后端开发', title: '腾讯后端高频问题复盘', content: '项目、网络、数据库与系统设计追问。', edit_time: null },
              { id: 2, company: '阿里巴巴', post: '后端开发', title: '阿里后端工程能力面经', content: 'Java、分布式、缓存与项目深挖。', edit_time: null },
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
