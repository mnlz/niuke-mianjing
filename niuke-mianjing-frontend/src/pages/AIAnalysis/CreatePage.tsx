import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Button, Checkbox, Empty, Input, message, Modal, Select, Spin, Upload } from 'antd'
import { ArrowLeftOutlined, ArrowRightOutlined, CheckOutlined, EyeOutlined, FilePdfOutlined, RobotOutlined, UploadOutlined } from '@ant-design/icons'
import { useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { logApi, recruitmentApi } from '@/api'
import type { AIModelPublic, ParsedResume, RecruitmentInterview, RecruitmentJob, RecruitmentSource, RecruitmentTrack, RecruitmentType } from '@/api/types'
import { getUserToken, userLoginPath } from '@/utils/auth'
import { formatDisplayTime } from '@/utils/datetime'
import AnalysisHeader from './AnalysisHeader'
import ResumeEditor from './ResumeEditor'
import { buildAnalysisRequest, generationBlocker, resumeRequirementError, toggleInterviewId, type AnalysisConfig } from './analysisUtils'
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
const reportCodes = ['COMPANY', 'COMPARE', 'INTERVIEW', 'RESUME', 'FULL SCAN', 'REVERSE']
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
  const [models, setModels] = useState<AIModelPublic[]>([])
  const [reportType, setReportType] = useState<ReportType>(initialType)
  const [source, setSource] = useState(searchParams.get('source') || 'tencent')
  const [compareSources, setCompareSources] = useState<string[]>(['tencent', 'meituan', 'bytedance'])
  const [recruitmentType, setRecruitmentType] = useState<RecruitmentType>((searchParams.get('type') as RecruitmentType) || 'campus')
  const [track, setTrack] = useState(searchParams.get('track') || 'backend')
  const [jobs, setJobs] = useState<RecruitmentJob[]>([])
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get('source_job_id') || searchParams.get('job_id') || '')
  const [interviews, setInterviews] = useState<RecruitmentInterview[]>([])
  const [selectedInterviewIds, setSelectedInterviewIds] = useState<number[]>(queryIds)
  const [resume, setResume] = useState('')
  const [resumeName, setResumeName] = useState('')
  const [resumePreviewUrl, setResumePreviewUrl] = useState('')
  const [resumePreviewOpen, setResumePreviewOpen] = useState(false)
  const resumePreviewUrlRef = useRef('')
  const [parsedResume, setParsedResume] = useState<ParsedResume | null>(null)
  const [resumeConfirmed, setResumeConfirmed] = useState(false)
  const [selectedModelId, setSelectedModelId] = useState<number | null>(null)
  const [jobLoading, setJobLoading] = useState(false)
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
  const activeJob = jobs.find((item) => item.source_job_id === selectedJobId)

  useEffect(() => {
    recruitmentApi.sources().then((data) => {
      setSources(data || [])
      const defaults = (data || []).filter((item) => item.supported_recruitment_types?.includes(recruitmentType))
        .map((item) => item.source).filter((item) => ['tencent', 'meituan', 'bytedance', 'jd'].includes(item)).slice(0, 4)
      if (defaults.length >= 2) setCompareSources(defaults)
    }).catch(() => setSources([]))
    recruitmentApi.tracks().then(setTracks).catch(() => setTracks([]))
    recruitmentApi.aiModels().then((data) => {
      setModels(data || [])
      setSelectedModelId((current) => (data || []).some((item) => item.id === current)
        ? current
        : (data || []).find((item) => item.is_default)?.id || data?.[0]?.id || null)
    }).catch(() => { setModels([]); setSelectedModelId(null) })
  }, [])

  useEffect(() => {
    window.localStorage.setItem('offerlens.ai-draft.v1', JSON.stringify({ reportType, source, compareSources, recruitmentType, track, selectedJobId, selectedModelId }))
  }, [reportType, source, compareSources, recruitmentType, track, selectedJobId, selectedModelId])

  useEffect(() => () => {
    if (resumePreviewUrlRef.current) URL.revokeObjectURL(resumePreviewUrlRef.current)
  }, [])

  useEffect(() => {
    if (compareMode) {
      setJobs([])
      setSelectedJobId('')
      return
    }
    setJobLoading(true)
    recruitmentApi.jobs({ source, recruitment_type: recruitmentType, track, page: 1, page_size: 24 }).then((data) => {
      const items = data.items || []
      setJobs(items)
      setSelectedJobId((current) => items.some((item) => item.source_job_id === current) ? current : items[0]?.source_job_id || '')
    }).catch(() => {
      setJobs([])
      setSelectedJobId('')
    }).finally(() => setJobLoading(false))
  }, [compareMode, source, recruitmentType, track])

  useEffect(() => {
    if (!interviewMode || (!compareMode && !selectedJobId)) {
      setInterviews([])
      setSelectedInterviewIds([])
      return
    }
    setInterviewLoading(true)
    const request = queryIds.length
      ? Promise.all(queryIds.slice(0, 12).map((id) => logApi.record(id))).then((items) => items.map((item) => ({
        id: item.id, content_id: item.content_id, title: item.title, company: item.company,
        post: item.post, edit_time: item.edit_time, read: item.read, status: item.status,
      })))
      : selectedJobId
        ? recruitmentApi.interviews({ source, recruitment_type: recruitmentType, source_job_id: selectedJobId, limit: 12 })
        : recruitmentApi.trackInterviews({ source, recruitment_type: recruitmentType, track, limit: 12 })
    request.then((items) => {
      setInterviews(items || [])
      setSelectedInterviewIds((items || []).slice(0, 12).map((item) => item.id))
    }).catch(() => {
      setInterviews([])
      setSelectedInterviewIds([])
    }).finally(() => setInterviewLoading(false))
  }, [interviewMode, compareMode, source, recruitmentType, track, selectedJobId, queryIds])

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
      if (resumePreviewUrlRef.current) URL.revokeObjectURL(resumePreviewUrlRef.current)
      const previewUrl = URL.createObjectURL(file)
      resumePreviewUrlRef.current = previewUrl
      setResumePreviewUrl(previewUrl)
      message.success('简历解析完成')
    } catch (error: unknown) {
      message.error((error as Error).message || '简历解析失败')
    }
    return false
  }

  const config: AnalysisConfig = {
    reportType, source, company: companyName, compareSources, recruitmentType, track,
    trackName: activeTrack?.name || track, sourceJobId: selectedJobId, interviewIds: selectedInterviewIds.slice(0, 12), resume, modelId: selectedModelId || 0,
  }

  const validate = () => {
    if (compareMode && compareSources.length < 2) return '请至少选择 2 家公司'
    if (!compareMode && !selectedJobId) return '请选择具体目标岗位'
    if (interviewMode && !selectedInterviewIds.length) return '请至少选择 1 篇面经'
    const resumeError = resumeRequirementError(resumeMode, resume, resumeConfirmed)
    if (resumeError) return resumeError
    if (!selectedModelId) return '请选择分析模型'
    return ''
  }

  const validationMessage = validate()
  const previewItems = [
    { label: '分析场景', value: reportTypeMeta(reportType).label, detail: reportTypeMeta(reportType).desc },
    { label: '目标公司', value: companyName, detail: compareMode ? `已选择 ${compareSources.length} 家公司进行对标` : '读取该公司最新官方招聘数据' },
    { label: '目标岗位', value: activeJob?.title || `${activeTrack?.name || track} · ${recruitmentTypeName(recruitmentType)}`, detail: activeJob ? `${activeJob.location || '地点未注明'} · 使用该岗位完整职责与要求` : '等待选择具体岗位' },
    { label: '面经样本', value: interviewMode ? `${selectedInterviewIds.length} 篇` : '本场景不使用', detail: interviewMode ? '用于提炼高频问题与面试侧重点' : '报告主要依据岗位数据生成' },
    { label: '个人简历', value: resume.trim() ? (parsedResume?.name || resumeName || '已提供') : resumeMode ? '待上传' : '本场景不使用', detail: resume.trim() ? `${parsedResume?.page_count || '—'} 页 · ${parsedResume?.sections.length || 0} 个分区 · ${resumeConfirmed ? '已确认' : '待确认'}` : '上传后将展示基本信息和分区摘要' },
    { label: '分析模型', value: (() => { const item = models.find((model) => model.id === selectedModelId); return item ? `${item.model} · ${item.channel_name}` : '待选择' })(), detail: models.find((item) => item.id === selectedModelId)?.description || '使用所选模型生成报告' },
    { label: '生成确认', value: validationMessage || '配置完整', detail: validationMessage ? '完成缺失项后即可生成报告' : '报告将保存到当前账号' },
  ]

  const changeResume = (value: string) => {
    setResume(value)
    setResumeConfirmed(false)
  }

  const changeStructuredResume = (value: string, parsed: ParsedResume) => {
    setResume(value)
    setParsedResume(parsed)
    setResumeConfirmed(false)
  }

  const applyRawResume = (value: string) => {
    setResume(value)
    setParsedResume(null)
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
          <div><span>ANALYSIS SETUP · {stepHeading(step)}</span><h1>{step === 5 && resume.trim() ? '确认你的简历内容' : '新建分析报告'}</h1><p>{step === 5 && resume.trim() ? '系统已解析简历并抽取分区。检查、修改后确认，即可进入下一步。' : '按步骤组合本次分析要使用的数据，完成后生成专属求职报告。'}</p></div>
          <div className="ai-create-title-actions"><small className="ai-save-status"><i /> 草稿已自动保存 · 刚刚</small><Button>保存草稿</Button></div>
        </div>

        <nav className="ai-horizontal-steps" aria-label="分析配置步骤">
          {stepNames.map((name, index) => {
            const number = index + 1
            return (
              <button key={name} className={number === step ? 'active' : number < step ? 'done' : ''} aria-current={number === step ? 'step' : undefined} onClick={() => setStep(number)}>
                <i>{number < step ? <CheckOutlined /> : number}</i><span><b>{name}</b><small>{String(number).padStart(2, '0')}{number === step ? ' · 当前' : ''}</small></span>
              </button>
            )
          })}
        </nav>

        <div className="ai-wizard-layout">
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
                {!compareMode && <label className="ai-field"><span>投递的具体岗位</span><Select size="large" showSearch optionFilterProp="label" loading={jobLoading} value={selectedJobId || undefined} onChange={setSelectedJobId} placeholder="选择简历投递的岗位" options={jobs.map((item) => ({ label: `${item.title}${item.location ? ` · ${item.location}` : ''}`, value: item.source_job_id }))} /></label>}
              </div>
            )}

            {step === 4 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(4)}</span><h2>选择面经样本</h2><p>{interviewMode ? '已按公司和岗位方向匹配近期面经，可手动排除不相关内容。' : '当前分析场景不强制使用面经，你可以直接进入下一步。'}</p></div>
                {!interviewMode ? <div className="ai-step-not-needed"><CheckOutlined /> {reportTypeMeta(reportType).label} 将主要使用岗位数据，无需额外选择面经。</div> : interviewLoading ? <Spin /> : interviews.length ? (
                  <>
                    <div className="ai-list-toolbar"><span>已选择 {selectedInterviewIds.length} 篇（最多 12 篇）</span><Button type="link" onClick={() => setSelectedInterviewIds(selectedInterviewIds.length ? [] : interviews.slice(0, 12).map((item) => item.id))}>{selectedInterviewIds.length ? '取消选择' : '选择全部'}</Button></div>
                    <div className="ai-interview-list create">
                      {interviews.map((item) => (
                        <label key={item.id}><Checkbox checked={selectedInterviewIds.includes(item.id)} onChange={(event) => {
                          if (event.target.checked && selectedInterviewIds.length >= 12) message.info('每份报告最多使用 12 篇面经')
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
              <div className={`ai-step-content${resume.trim() ? ' ai-resume-step-content' : ''}`}>
                {!resumeMode && <div className="ai-step-not-needed"><CheckOutlined /> 你可以跳过本步，或返回第一步选择包含简历的分析类型。</div>}
                {resume.trim() ? (
                  <div className="ai-resume-result">
                    <div className="ai-resume-result-head">
                      <div><span>RESUME PARSED · READY TO REVIEW</span><h2>简历解析结果</h2><p>系统已完成结构化抽取。请核对基本信息与 {parsedResume?.sections.length || 0} 个分区，随时点击卡片进行编辑。</p></div>
                      <div className="ai-resume-result-status"><em className={resumeConfirmed ? 'confirmed' : ''}>{resumeConfirmed ? '已确认' : '待确认'}</em><small>{parsedResume?.page_count || '—'} 页　{(parsedResume?.char_count || resume.trim().length).toLocaleString()} 字　{parsedResume?.sections.length || 0} 分区</small></div>
                    </div>
                    <div className="ai-resume-file-row">
                      <div className="ai-resume-file-content"><FilePdfOutlined /><span><b>{resumeName || '粘贴的简历文本'}</b><small>{resumePreviewUrl ? 'PDF　·　解析完成　·　可预览原文件' : '文本内容　·　解析完成'}</small></span></div>
                      <div className="ai-resume-file-actions">
                        <Button icon={<EyeOutlined />} disabled={!resumePreviewUrl} onClick={() => setResumePreviewOpen(true)}>预览简历</Button>
                        <Upload accept="application/pdf,.pdf" maxCount={1} beforeUpload={(file) => parseResume(file as File)} showUploadList={false}><Button>重新上传</Button></Upload>
                      </div>
                    </div>
                    {parsedResume?.sections.length ? <ResumeEditor resume={resume} parsedResume={parsedResume} onChange={changeStructuredResume} onRawApply={applyRawResume} /> : <label className="ai-resume-editor plain parsed"><span>原文编辑模式</span><Input.TextArea value={resume} onChange={(event) => changeResume(event.target.value)} rows={14} /></label>}
                    <div className="ai-resume-confirm">
                      <p>确认后系统才会把以上内容用于岗位匹配和报告生成；再次编辑会自动撤销确认。</p>
                      <Button type={resumeConfirmed ? 'default' : 'primary'} icon={<CheckOutlined />} onClick={() => setResumeConfirmed(true)} disabled={resumeConfirmed}>确认使用此简历</Button>
                    </div>
                  </div>
                ) : (
                  <><div className="ai-step-heading"><span>{stepHeading(5)}</span><h2>上传个人简历</h2><p>{resumeMode ? '系统会将你的经历逐项映射到岗位要求，并给出修改建议。' : '当前场景不要求简历；加入简历可切换到简历诊断或完整分析。'}</p></div><Upload.Dragger className="ai-resume-drop" accept="application/pdf,.pdf" maxCount={1} beforeUpload={(file) => parseResume(file as File)} showUploadList={false}><UploadOutlined /><b>上传 PDF 简历</b><small>点击或拖拽文件到这里，最大 8 MB</small></Upload.Dragger><label className="ai-resume-editor plain"><span>或直接粘贴简历文本</span><Input.TextArea value={resume} onChange={(event) => changeResume(event.target.value)} rows={9} placeholder="粘贴后会展示可编辑的解析结果……" /></label></>
                )}
              </div>
            )}

            {step === 6 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(6)}</span><h2>选择分析模型</h2><p>选择本次报告实际使用的模型。</p></div>
                <div className="ai-model-picker">
                  {models.map((model) => (
                    <button key={model.id} className={selectedModelId === model.id ? 'active' : ''} aria-pressed={selectedModelId === model.id} onClick={() => setSelectedModelId(model.id)}>
                      <i className="ai-model-code">MODEL</i>
                      <span className="ai-model-copy"><b>{model.model} · {model.channel_name}</b><small>{model.description || 'OpenAI 兼容分析模型'}</small></span>
                      {model.is_default && <em>默认</em>}
                      {selectedModelId === model.id && <strong><CheckOutlined /></strong>}
                    </button>
                  ))}
                </div>
                {!models.length && <div className="ai-step-not-needed"><RobotOutlined /> 当前没有可用模型，请联系管理员配置。</div>}
              </div>
            )}

            {step === 7 && (
              <div className="ai-step-content">
                <div className="ai-step-heading"><span>{stepHeading(7)}</span><h2>确认报告范围</h2><p>检查组合是否符合你的目标，生成后会自动保存到报告中心。</p></div>
                <div className="ai-confirm-list">
                  <div><span>分析类型</span><b>{reportTypeMeta(reportType).label}</b><em>{resumeMode && interviewMode ? '4 元素' : '专项'}</em></div>
                  <div><span>目标公司</span><b>{companyName}</b><em>{compareMode ? `${compareSources.length} 家` : '已确认'}</em></div>
                  <div><span>目标岗位</span><b>{activeJob?.title || `${activeTrack?.name || track} · ${recruitmentTypeName(recruitmentType)}`}</b><em>{activeJob ? '精确 JD' : '待选择'}</em></div>
                  <div><span>面经样本</span><b>{interviewMode ? `${selectedInterviewIds.length} 篇` : '不使用'}</b><em>近期样本</em></div>
                  <div><span>个人简历</span><b>{resumeMode ? (resumeConfirmed ? '已解析并确认' : resume.trim() ? '待确认' : '待提供') : '不使用'}</b><em>{resumeConfirmed ? '已确认' : '推荐'}</em></div>
                  <div><span>分析模型</span><b>{(() => { const item = models.find((model) => model.id === selectedModelId); return item ? `${item.model} · ${item.channel_name}` : '待选择' })()}</b><em>已配置</em></div>
                </div>
                <Button type="primary" size="large" icon={<RobotOutlined />} loading={generating} onClick={generate} block>生成精美分析报告</Button>
              </div>
            )}

            <div className="ai-wizard-actions">
              <Button icon={<ArrowLeftOutlined />} disabled={step === 1} onClick={() => setStep((value) => Math.max(1, value - 1))}>上一步</Button>
              {step < TOTAL_STEPS && <Button type="primary" onClick={() => setStep((value) => Math.min(TOTAL_STEPS, value + 1))}>下一步 <ArrowRightOutlined /></Button>}
            </div>
          </section>
          <aside className="ai-live-preview" aria-label="报告实时预览">
            <div className="ai-preview-label"><span>LIVE PREVIEW</span><em>SYNCING</em></div>
            <div className="ai-preview-card">
              <div className="preview-top"><b>OfferLens Report</b><small>STEP {String(step).padStart(2, '0')} / 07</small></div>
              <div className="preview-main">
                <span>{reportTypeMeta(reportType).label}</span>
                <h3>{companyName}</h3>
                <p>{activeJob?.title || `${activeTrack?.name || track} · ${recruitmentTypeName(recruitmentType)}`}</p>
                <div className="preview-metrics"><div><span>当前进度</span><b>{step} / 7</b></div><div><span>报告数据</span><b>{previewItems.slice(0, step).length} 项</b></div></div>
                <h4>已加入报告</h4>
                <div className="preview-progress-list">
                  {previewItems.slice(0, step).map((item, index) => <article key={item.label} className={index + 1 === step ? 'active' : ''}><i>{String(index + 1).padStart(2, '0')}</i><div><span>{item.label}</span><b>{item.value}</b><small>{item.detail}</small></div></article>)}
                </div>
                <div className="preview-data"><CheckOutlined /> 预览随当前配置实时更新</div>
              </div>
            </div>
          </aside>
        </div>
      </main>
      <Modal className="ai-resume-preview-modal" title={resumeName || '简历预览'} open={resumePreviewOpen} onCancel={() => setResumePreviewOpen(false)} footer={null} width="min(920px, calc(100vw - 32px))" destroyOnClose>
        {resumePreviewUrl && <iframe className="ai-resume-preview-frame" src={resumePreviewUrl} title="预览简历 PDF" />}
      </Modal>
    </div>
  )
}

export default CreatePage
