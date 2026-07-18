import React, { useEffect, useState } from 'react'
import { Button, Input } from 'antd'
import { CheckOutlined, EditOutlined } from '@ant-design/icons'
import type { ParsedResume } from '@/api/types'
import { replaceFirstText } from './analysisUtils'

interface ResumeEditorProps {
  resume: string
  parsedResume: ParsedResume
  onChange: (resume: string, parsedResume: ParsedResume) => void
  onRawApply: (resume: string) => void
}

const ResumeEditor: React.FC<ResumeEditorProps> = ({ resume, parsedResume, onChange, onRawApply }) => {
  const [editingSection, setEditingSection] = useState<number | null>(null)
  const [activeSection, setActiveSection] = useState(0)
  const [rawDraft, setRawDraft] = useState(resume)

  useEffect(() => setRawDraft(resume), [resume])

  const updateProfile = (field: 'name' | 'email' | 'phone', next: string) => {
    const previous = parsedResume[field] || ''
    const text = previous ? replaceFirstText(resume, previous, next) : `${next}\n${resume}`
    onChange(text, { ...parsedResume, [field]: next, char_count: text.length })
  }

  const updateSection = (index: number, content: string) => {
    const current = parsedResume.sections[index]
    const sections = parsedResume.sections.map((section, sectionIndex) => sectionIndex === index ? { ...section, content } : section)
    const text = replaceFirstText(resume, current.content, content)
    onChange(text, { ...parsedResume, sections, char_count: text.length })
  }

  return (
    <div className="ai-resume-structured-editor">
      <section className="ai-resume-profile-editor">
        <div className="ai-resume-editor-title"><div><b>基本信息</b><small>检查解析结果，点击即可修改</small></div><span>PROFILE</span></div>
        <div className="ai-resume-profile-grid">
          <label><span>姓名</span><Input value={parsedResume.name || ''} onChange={(event) => updateProfile('name', event.target.value)} placeholder="请输入姓名" /></label>
          <label><span>邮箱</span><Input value={parsedResume.email || ''} onChange={(event) => updateProfile('email', event.target.value)} placeholder="请输入邮箱" /></label>
          <label><span>手机号</span><Input value={parsedResume.phone || ''} onChange={(event) => updateProfile('phone', event.target.value)} placeholder="请输入手机号" /></label>
        </div>
      </section>

      <section className="ai-resume-section-editor">
        <div className="ai-resume-editor-title"><div><b>简历正文</b><small>{parsedResume.sections.length} 个已识别分区</small></div><span>CONTENT</span></div>
        <div className="ai-resume-section-tabs" role="tablist" aria-label="简历分区">
          {parsedResume.sections.map((section, index) => <button key={`${section.key}-${index}`} className={activeSection === index ? 'active' : ''} role="tab" aria-selected={activeSection === index} onClick={() => { setActiveSection(index); setEditingSection(null) }}><i>{String(index + 1).padStart(2, '0')}</i><b>{section.title}</b><small>{section.content.split(/\n+/).filter(Boolean).length}</small></button>)}
        </div>
        <div className="ai-resume-section-list">
          {[parsedResume.sections[activeSection]].map((section) => {
            const index = activeSection
            const editing = editingSection === activeSection
            return (
              <article className={`ai-resume-section-card${editing ? ' editing' : ''}`} key={`${section.key}-${index}`}>
                <header><div><i>{String(index + 1).padStart(2, '0')}</i><b>{section.title}</b></div><Button type="text" size="small" icon={editing ? <CheckOutlined /> : <EditOutlined />} onClick={() => setEditingSection(editing ? null : index)}>{editing ? '完成' : '编辑'}</Button></header>
                {editing ? (
                  <Input.TextArea aria-label={`编辑${section.title}`} value={section.content} onChange={(event) => updateSection(index, event.target.value)} autoSize={{ minRows: 5, maxRows: 14 }} />
                ) : (
                  <div className="ai-resume-section-copy">{section.content.split(/\n+/).filter(Boolean).map((line, lineIndex) => <p key={lineIndex}>{line}</p>)}</div>
                )}
              </article>
            )
          })}
        </div>
      </section>

      <details className="ai-resume-raw-editor">
        <summary><div><b>高级编辑</b><small>解析异常时直接修改原始文本</small></div><span>RAW TEXT</span></summary>
        <div><p>应用后将切换为原文编辑模式；报告会使用下方完整内容。</p><Input.TextArea aria-label="原始简历文本" value={rawDraft} onChange={(event) => setRawDraft(event.target.value)} rows={12} /><Button onClick={() => onRawApply(rawDraft)}>应用原文修改</Button></div>
      </details>
    </div>
  )
}

export default ResumeEditor
