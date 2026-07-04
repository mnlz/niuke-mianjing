import type { RecruitmentType } from '@/api/types'

export const recruitmentTypeOptions: Array<{ label: string; value: RecruitmentType }> = [
  { label: '校招', value: 'campus' },
  { label: '实习', value: 'intern' },
  { label: '社招', value: 'social' },
]

export const recruitmentTypeName = (value?: string) =>
  recruitmentTypeOptions.find((item) => item.value === value)?.label || value || '校招'

export const recruitmentSourceLogos: Record<string, string> = {
  alibaba: '/company-logos/阿里巴巴.svg',
  baidu: '/company-logos/icon_百度logo.svg',
  bytedance: '/company-logos/字节跳动.svg',
  huawei: '/company-logos/华为.svg',
  jd: '/company-logos/jd.svg',
  kuaishou: '/company-logos/快手.svg',
  meituan: '/company-logos/美团.svg',
  tencent: '/company-logos/腾讯-01.svg',
}
