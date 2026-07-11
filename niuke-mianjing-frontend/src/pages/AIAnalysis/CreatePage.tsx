import React, { useEffect, useMemo, useState } from 'react'
import { Button, Checkbox, Empty, Input, message, Select, Spin, Tag, Upload } from 'antd'
import { ArrowLeftOutlined, ArrowRightOutlined, CheckOutlined, FilePdfOutlined, RobotOutlined, UploadOutlined } from '@ant-design/icons'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { logApi, recruitmentApi } from '@/api'
import type { ParsedResume, RecruitmentInterview, RecruitmentSource, RecruitmentTrack, RecruitmentType } from '@/api/types'
import { getUserToken, userLoginPath } from '@/utils/auth'
import { formatDisplayTime } from '@/utils/datetime'
import AnalysisHeader from './AnalysisHeader'
import { buildAnalysisRequest, extractResumeContacts, generationBlocker, resumeRequirementError, toggleInterviewId, type AnalysisConfig } from './analysisUtils'
import {
  isCompanyCompare,
  needsInterviews,
  needsResume,
  recruitmentTypeName,
  recruitmentTypes,
  reportTypeMeta,
  reportTypes,
  type ReportType,
} from './config'
import './style.css'

const TOTAL_STEPS = 7
const stepNames = ['分析类型', '目标公司', '目标岗位', '面经范围', '个人简历', '分析模型', '确认生成']
const stepDetails = ['选择一个报告场景', '选择已接入公司', '校招 / 社招 / 实习', '匹配近期真实面经', '解析并确认内容', '选择分析模型', '预计约 60 秒']
const reportCodes = ['COMPANY', 'COMPARE', 'INTERVIEW', 'RESUME', 'FULL SCAN', 'REVERSE']
const mockModels = [
  { value: 'gpt-5.4-mini', label: 'GPT-5.4 Mini', desc: '响应更快，适合快速了解岗位与面试重点' },
  { value: 'gpt-5.5', label: 'GPT-5.5', desc: '分析速度与报告深度均衡', recommended: true },
  { value: 'gpt-5.6-sol', label: 'GPT-5.6 Sol', desc: '更深入地梳理岗位、面经与简历关联' },
]
const stepHeading = (value: number) => `STEP ${String(value).padStart(2, '0')} / ${String(TOTAL_STEPS).padStart(2, '0')}`
const parseIds = (value: string | null) => (value || '').split(',').map(Number).filter((id) => Number.isInteger(id) && id > 0)
const isReportType = (value: string | null): value is ReportType => reportTypes.some((item) => item.value === value)

const CreatePage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [searchParams] = useSearchParams()
  const requestedType = searchParams.get('report')
  const initialType: ReportType = isReportType(requestedType) ? requestedType : 'full'
  const queryIds = useMemo(() => parseIds(searchParams.get('ids') || searchParams.get('interview_ids')), [searchParams])
  const [step, setStep] = useState(1)
  const [sources, setSources] = useState<RecruitmentSource[]>([])
  const [tracks, setTracks] = useState<RecruitmentTrack[]>([])
  const [reportType, setReportType] = useState<ReportType>(initialType)
  const [source, setSource] = useState(searchParams.get('source') || 'tencent')
  const [compareSources, setCompareSources] = useState<string[]>(['tencent', 'meituan', 'bytedance'])
  const [recruitmentType, setRecruitmentType] = useState<RecruitmentType>((searchParams.get('type') as RecruitmentType) || 'campus')
  const [track, setTrack] = useState(searchParams.get('track') || 'backend')
  const [interviews, setInterviews] = useState<RecruitmentInterview[]>([])
  const [selectedInterviewIds, setSelectedInterviewIds] = useState<number[]>(queryIds)
  const [resume, setResume] = useState('')
  const [resumeName, setResumeName] = useState('')
  const [parsedResume, setParsedResume] = useState<ParsedResume | null>(null)
  const [resumeConfirmed, setResumeConfirmed] = useState(false)
  const [selectedModel, setSelectedModel] = useState('gpt-5.5')
  const [interviewLoading, setInterviewLoading] = useState(false)
  const [generating, setGenerating] = useState(false)

  const compareMode = isCompanyCompare(reportType)
  const interviewMode = needsInterviews(reportType)
  const resumeMode = needsResume(reportType)
  const activeSource = sources.find((item) => item.source === source)
  const activeTrack = tracks.find((item) => item.id === track)
  const supportedTypes = recruitmentTypes.filter((item) => !activeSource?.supported_recruitment_types?.length || activeSource.supported_recruitment_types.includes(item.value))
  const selectedCompanyNames = sources.filter((item) => compareSources.includes(item.source)).map((item) => item.company)
  const companyName = compareMode ? selectedCompanyNames.join('、') || '多公司' : activeSource?.company || source
  const resumeContacts = useMemo(() => extractResumeContacts(resume), [resume])

  useEffect(() => {
    recruitmentApi.sources().then((data) => {
      setSources(data || [])
      const defaults = (data || []).filter((item) => item.supported_recruitment_types?.includes(recruitmentType))
        .map((item) => item.source).filter((item) => ['tencent', 'meituan', 'bytedance', 'jd'].includes(item)).slice(0, 4)
      if (defaults.length >= 2) setCompareSources(defaults)
    }).catch(() => setSources([]))
    recruitmentApi.tracks().then(setTracks).catch(() => setTracks([]))
  }, [])

  useEffect(() => {
    window.localStorage.setItem('offerlens.ai-draft.v1', JSON.stringify({ reportType, source, compareSources, recruitmentType, track, selectedModel }))
  }, [reportType, source, compareSources, recruitmentType, track, selectedModel])

  useEffect(() => {
    if (!interviewMode) {
      setInterviews([])
      setSelectedInterviewIds([])
      return
    }
    setInterviewLoading(true)
    const request = queryIds.length
      ? Promise.all(queryIds.slice(0, 8).map((id) => logApi.record(id))).then((items) => items.map((item) => ({
        id: item.id, content_id: item.content_id, title: item.title, company: item.company,
        post: item.post, edit_time: item.edit_time, read: item.read, status: item.status,
      })))
      : recruitmentApi.trackInterviews({ source, recruitment_type: recruitmentType, track, limit: 12 })
    request.then((items) => {
      setInterviews(items || [])
      setSelectedInterviewIds((items || []).slice(0, 8).map((item) => item.id))
    }).catch(() => {
      setInterviews([])
      setSelectedInterviewIds([])
    }).finally(() => setInterviewLoading(false))
  }, [interviewMode, source, recruitmentType, track, queryIds])

  const changeSource = (value: string) => {
    const meta = sources.find((item) => item.source === value)
    const nextType = meta?.supported_recruitment_types?.includes(recruitmentType)
      ? recruitmentType
      : (meta?.supported_recruitment_types?.[0] as RecruitmentType) || recruitmentType
    setSource(value)
    setRecruitmentType(nextType)
  }

  const changeRecruitmentType = (value: RecruitmentType) => {
    setRecruitmentType(value)
    setCompareSources((current) => current.filter((item) => sources.find((sourceItem) => sourceItem.source === item)?.supported_recruitment_types?.includes(value)))
  }

  const parseResume = async (file: File) => {
    if (!getUserToken()) {
      message.warning('登录后可以解析简历')
      navigate(userLoginPath(`${location.pathname}${location.search}`))
      return false
    }
    try {
      const result = await recruitmentApi.parseResume(file)
      setResume(result.text)
      setResumeName(file.name)
      setParsedResume(result)
      setResumeConfirmed(false)
      message.success('简历解析完成')
    } catch (error: unknown) {
      message.error((error as Error).message || '简历解析失败')
    }
    return false
  }

  const config: AnalysisConfig = {
    reportType, source, company: companyName, compareSources, recruitmentType, track,
    trackName: activeTrack?.name || track, interviewIds: selectedInterviewIds.slice(0, 8), resume,
  }

  const validate = () => {
    if (compareMode && compareSources.length < 2) return '请至少选择 2 家公司'
    if (interviewMode && !selectedInterviewIds.length) return '请至少选择 1 篇面经'
    const resumeError = resumeRequirementError(resumeMode, resume, resumeConfirmed)
    if (resumeError) return resumeError
    return ''
  }

  const changeResume = (value: string) => {
    setResume(value)
    setResumeConfirmed(false)
  }

  const generate = async () => {
    const invalid = generationBlocker(Boolean(getUserToken()), validate())
    if (invalid === 'login') {
      message.warning('登录后可以生成 AI 报告')
      navigate(userLoginPath(`${location.pathname}${location.search}`))
      return
    }
    if (invalid) {
      message.warning(invalid)
      return
    }
    try {
      setGenerating(true)
      const result = await recruitmentApi.aiReport(buildAnalysisRequest(config))
      navigate(`/ai-analysis/reports?id=${encodeURIComponent(result.report_code)}`)
    } catch (error: unknown) {
      message.error((error as Error).message || 'AI 报告生成失败')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="ai-product-page ai-create-page">
      <AnalysisHeader active="create" />
      <main>
        <div className="ai-create-title">
          <div><span>ANALYSIS SETUP</span><h1>新建分析报告</h1><p>按步骤组合本次分析要使用的数据，右侧会同步显示报告范围。</p></div>
          <small className="ai-save-status"><i /> 自动保存 · 刚刚</small>
        </div>

        <div className="ai-wizard-layout">
          <aside className="ai-step-nav">
            <div className="ai-step-progress"><span>配置进度</span><b>{step} / {TOTAL_STEPS}</b><div><i style={{ width: `${step / TOTAL_STEPS * 100}%` }} /></div></div>
            {stepNames.map((name, index) => {
              const number = index + 1
              return (
                <button key={name} className={number === step ? 'active' : number < step ? 'done' : ''} aria-current={number === step ? 'step' : undefined} onClick={() => setStep(number)}>
                  <i>{number < step ? <CheckOutlined /> : number}</i><span><b>{name}</b><small>{stepDetails[index]}</small></span>
                </button>
              )
            })}
            <div className="ai-draft-note"><CheckOutlined /> 配置已自动保存在当前浏览器</div>
          </aside>

          <section className="ai-wizard-panel">
            {step === 1 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(1)}</span><h2>这次你想解决什么问题？</h2><p>先选场景，后面的步骤会自动提示需要哪些数据。</p></div>
                <div className="ai-type-picker">
                  {reportTypes.map((item, index) => (
                    <button key={item.value} className={reportType === item.value ? 'active' : ''} aria-pressed={reportType === item.value} onClick={() => setReportType(item.value)}>
                      <i className="ai-type-code">{item.icon} // {reportCodes[index]}</i><span className="ai-type-copy"><b>{item.label}</b><small>{item.desc}</small></span>{item.featured && <em>推荐</em>}<strong><CheckOutlined /></strong>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(2)}</span><h2>{compareMode ? '选择需要比较的公司' : '选择目标公司'}</h2><p>仅展示当前已经接入官方招聘数据的公司。</p></div>
                <div className="ai-company-picker">
                  {sources.map((item) => {
                    const selected = compareMode ? compareSources.includes(item.source) : item.source === source
                    return (
                      <button key={item.source} className={selected ? 'active' : ''} aria-pressed={selected} onClick={() => {
                        if (compareMode) setCompareSources((current) => selected ? current.filter((value) => value !== item.source) : [...current, item.source])
                        else changeSource(item.source)
                      }}>
                        {item.logo ? <img src={item.logo} alt="" /> : <span>{item.company.slice(0, 1)}</span>}
                        <b>{item.company}</b><small>{item.supported_recruitment_types?.length || 0} 类招聘</small>{selected && <CheckOutlined />}
                      </button>
                    )
                  })}
                </div>
              </div>
            )}

            {step === 3 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(3)}</span><h2>圈定岗位方向</h2><p>系统会从所选公司中提取这个方向的岗位职责和任职要求。</p></div>
                <label className="ai-field"><span>招聘类型</span><Select size="large" value={recruitmentType} onChange={changeRecruitmentType} options={compareMode ? recruitmentTypes : supportedTypes} /></label>
                <label className="ai-field"><span>岗位方向</span><Select size="large" value={track} onChange={setTrack} options={tracks.map((item) => ({ label: item.name, value: item.id }))} /></label>
                <div className="ai-track-picker">
                  {tracks.map((item) => <button key={item.id} className={track === item.id ? 'active' : ''} aria-pressed={track === item.id} onClick={() => setTrack(item.id)}><b>{item.name}</b><small>{item.description}</small></button>)}
                </div>
              </div>
            )}

            {step === 4 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(4)}</span><h2>选择面经样本</h2><p>{interviewMode ? '已按公司和岗位方向匹配近期面经，可手动排除不相关内容。' : '当前分析场景不强制使用面经，你可以直接进入下一步。'}</p></div>
                {!interviewMode ? <div className="ai-step-not-needed"><CheckOutlined /> {reportTypeMeta(reportType).label} 将主要使用岗位数据，无需额外选择面经。</div> : interviewLoading ? <Spin /> : interviews.length ? (
                  <>
                    <div className="ai-list-toolbar"><span>已选择 {selectedInterviewIds.length} 篇（最多 8 篇）</span><Button type="link" onClick={() => setSelectedInterviewIds(selectedInterviewIds.length ? [] : interviews.slice(0, 8).map((item) => item.id))}>{selectedInterviewIds.length ? '取消选择' : '选择前 8 篇'}</Button></div>
                    <div className="ai-interview-list create">
                      {interviews.map((item) => (
                        <label key={item.id}><Checkbox checked={selectedInterviewIds.includes(item.id)} onChange={(event) => {
                          if (event.target.checked && selectedInterviewIds.length >= 8) message.info('每份报告最多使用 8 篇面经')
                          setSelectedInterviewIds((current) => toggleInterviewId(current, item.id, event.target.checked))
                        }} />
                          <span><b>{item.title}</b><small>{item.company} · {item.post || '面经'} · {formatDisplayTime(item.edit_time)}</small></span><em>{selectedInterviewIds.includes(item.id) ? '强相关' : '相关'}</em></label>
                      ))}
                    </div>
                  </>
                ) : <Empty description="暂未匹配到该方向的面经" />}
              </div>
            )}

            {step === 5 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(5)}</span><h2>加入个人简历</h2><p>{resumeMode ? '系统会将你的经历逐项映射到岗位要求，并给出修改建议。' : '当前场景不要求简历；加入简历可切换到简历诊断或完整分析。'}</p></div>
                {!resumeMode && <div className="ai-step-not-needed"><CheckOutlined /> 你可以跳过本步，或返回第一步选择包含简历的分析类型。</div>}
                <Upload.Dragger className="ai-resume-drop" accept="application/pdf,.pdf" maxCount={1} beforeUpload={(file) => parseResume(file as File)} showUploadList={false}>
                  {resumeName ? <><FilePdfOutlined /><b>{resumeName}</b><small>重新上传会替换当前解析结果</small></> : <><UploadOutlined /><b>上传 PDF 简历</b><small>点击或拖拽文件到这里，最大 8 MB</small></>}
                </Upload.Dragger>
                {resume.trim() ? (
                  <div className="ai-resume-result">
                    <div className="ai-resume-result-head">
                      <div><span>简历解析结果</span><h3>{resumeName || '粘贴的简历文本'}</h3></div>
                      <Tag color={resumeConfirmed ? 'green' : 'gold'}>{resumeConfirmed ? '已确认' : '待确认'}</Tag>
                    </div>
                    <div className="ai-resume-meta">
                      <span><small>姓名</small><b>{parsedResume?.name || '未识别'}</b></span>
                      <span><small>邮箱</small><b>{parsedResume?.email || resumeContacts.email || '未识别'}</b></span>
                      <span><small>手机号</small><b>{parsedResume?.phone || resumeContacts.phone || '未识别'}</b></span>
                      <span><small>PDF 页数</small><b>{parsedResume ? `${parsedResume.page_count} 页` : '—'}</b></span>
                      <span><small>解析字数</small><b>{(parsedResume?.char_count || resume.trim().length).toLocaleString()}</b></span>
                    </div>
                    <div className="ai-resume-editor-panel">
                      <div className="ai-resume-editor-head">
                        <div><b>简历内容（可编辑）</b><small>修改后需重新确认</small></div>
                        {parsedResume?.sections.length ? <span>{parsedResume.sections.length} 个分区</span> : null}
                      </div>
                      {parsedResume?.sections.length ? (
                        <div className="ai-resume-section-tags" aria-label="识别到的简历分区">
                          {parsedResume.sections.map((section) => <span key={section.key}>{section.title}</span>)}
                        </div>
                      ) : null}
                      <Input.TextArea aria-label="简历内容（可编辑）" value={resume} onChange={(event) => changeResume(event.target.value)} rows={12} />
                    </div>
                    <div className="ai-resume-confirm">
                      <p>确认后系统才会把以上内容用于岗位匹配和报告生成；再次编辑会自动撤销确认。</p>
                      <Button type={resumeConfirmed ? 'default' : 'primary'} icon={<CheckOutlined />} onClick={() => setResumeConfirmed(true)} disabled={resumeConfirmed}>确认使用此简历</Button>
                    </div>
                  </div>
                ) : (
                  <label className="ai-resume-editor plain"><span>或直接粘贴简历文本</span><Input.TextArea value={resume} onChange={(event) => changeResume(event.target.value)} rows={9} placeholder="粘贴后会展示可编辑的解析结果……" /></label>
                )}
              </div>
            )}

            {step === 6 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(6)}</span><h2>选择分析模型</h2><p>选择你偏好的分析速度与深度，本次仅用于预览配置。</p></div>
                <div className="ai-model-picker">
                  {mockModels.map((model) => (
                    <button key={model.value} className={selectedModel === model.value ? 'active' : ''} aria-pressed={selectedModel === model.value} onClick={() => setSelectedModel(model.value)}>
                      <i className="ai-model-code">{model.value}</i>
                      <span className="ai-model-copy"><b>{model.label}</b><small>{model.desc}</small></span>
                      {model.recommended && <em>推荐</em>}
                      {selectedModel === model.value && <strong><CheckOutlined /></strong>}
                    </button>
                  ))}
                </div>
                <div className="ai-step-not-needed"><RobotOutlined /> 预览配置：实际生成仍使用系统当前配置的模型，后续接入真实模型切换。</div>
              </div>
            )}

            {step === 7 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(7)}</span><h2>确认报告范围</h2><p>检查组合是否符合你的目标，生成后会自动保存到报告中心。</p></div>
                <div className="ai-confirm-list">
                  <div><span>分析类型</span><b>{reportTypeMeta(reportType).label}</b><em>{resumeMode && interviewMode ? '4 元素' : '专项'}</em></div>
                  <div><span>目标公司</span><b>{companyName}</b><em>{compareMode ? `${compareSources.length} 家` : '已确认'}</em></div>
                  <div><span>岗位范围</span><b>{activeTrack?.name || track} · {recruitmentTypeName(recruitmentType)}</b><em>实时岗位</em></div>
                  <div><span>面经样本</span><b>{interviewMode ? `${selectedInterviewIds.length} 篇` : '不使用'}</b><em>近期样本</em></div>
                  <div><span>个人简历</span><b>{resumeMode ? (resumeConfirmed ? '已解析并确认' : resume.trim() ? '待确认' : '待提供') : '不使用'}</b><em>{resumeConfirmed ? '已确认' : '推荐'}</em></div>
                  <div><span>分析模型</span><b>{mockModels.find((model) => model.value === selectedModel)?.label}</b><em>预览配置</em></div>
                </div>
                <Button type="primary" size="large" icon={<RobotOutlined />} loading={generating} onClick={generate} block>生成精美分析报告</Button>
              </div>
            )}

            <div className="ai-wizard-actions">
              <Button icon={<ArrowLeftOutlined />} disabled={step === 1} onClick={() => setStep((value) => Math.max(1, value - 1))}>上一步</Button>
              {step < TOTAL_STEPS && <Button type="primary" onClick={() => setStep((value) => Math.min(TOTAL_STEPS, value + 1))}>下一步 <ArrowRightOutlined /></Button>}
            </div>
          </section>

          <aside className="ai-live-preview">
            <div className="ai-preview-label"><span>LIVE PREVIEW</span><Tag color="green">SYNCING</Tag></div>
            <div className="ai-preview-card">
              <div className="preview-top"><b>OfferLens Report</b><small># DRAFT</small></div>
              <div className="preview-main">
                <span>{reportTypeMeta(reportType).label}</span><h3>{companyName}</h3><p>{activeTrack?.name || track} · {recruitmentTypeName(recruitmentType)}</p>
                <div className="preview-metrics"><div><span>岗位数据</span><b>实时读取</b></div><div><span>面经样本</span><b>{interviewMode ? selectedInterviewIds.length : '—'}</b></div></div>
                <h4>本报告将回答</h4>
                <ul><li>这个方向最近在招什么、要求什么？</li><li>我的准备顺序应该如何安排？</li>{resumeMode && <li>简历与岗位有哪些匹配和缺口？</li>}{interviewMode && <li>近期面试最可能追问哪些问题？</li>}</ul>
                <div className="preview-data"><CheckOutlined /> 仅使用你在左侧确认的数据范围</div>
              </div>
            </div>
          </aside>
        </div>
      </main>
    </div>
  )
}

export default CreatePage
