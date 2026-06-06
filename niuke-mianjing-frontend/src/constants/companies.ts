export interface CompanyBrand {
  name: string
  logo: string
  slogan: string
  searchName?: string
}

export const companyBrands: CompanyBrand[] = [
  { name: '字节跳动', logo: '/company-logos/字节跳动.svg', slogan: '内容与算法高频' },
  { name: '腾讯', logo: '/company-logos/腾讯-01.svg', slogan: '后端与基础架构' },
  { name: '阿里巴巴', logo: '/company-logos/阿里巴巴.svg', slogan: 'Java 与工程能力' },
  { name: '美团', logo: '/company-logos/美团.svg', slogan: '业务系统与项目深挖' },
  { name: '百度', logo: '/company-logos/icon_百度logo.svg', slogan: '搜索与 AI 方向' },
  { name: '小米', logo: '/company-logos/小米.svg', slogan: '终端与互联网业务' },
  { name: '京东', logo: '/company-logos/jd.svg', slogan: '电商与供应链系统' },
  { name: '快手', logo: '/company-logos/快手.svg', slogan: '推荐与直播业务' },
  { name: '滴滴', logo: '/company-logos/滴滴.svg', slogan: '出行与调度系统' },
  { name: '网易', logo: '/company-logos/网易.svg', slogan: '游戏与内容平台' },
  { name: '华为', logo: '/company-logos/华为.svg', slogan: '终端、云与基础软件' },
  { name: '拼多多', logo: '/company-logos/拼多多.svg', slogan: '电商与增长系统' },
  { name: 'B站', logo: '/company-logos/B站.svg', slogan: '内容社区与推荐', searchName: 'B站' },
  { name: '高德地图', logo: '/company-logos/高德地图-全.svg', slogan: '地图与位置服务' },
  { name: '微博', logo: '/company-logos/微博.svg', slogan: '社交媒体与内容平台' },
  { name: 'MiniMax', logo: '/company-logos/minimax.svg', slogan: '大模型与智能体应用' },
  { name: '智谱 AI', logo: '/company-logos/智谱logo.svg', slogan: '国产大模型与知识工程', searchName: '智谱' },
  { name: 'DeepSeek', logo: '/company-logos/deepseek-copy.svg', slogan: '推理模型与算法工程' },
]

export const hotInterviewCompanies = companyBrands.filter((company) =>
  ['字节跳动', '腾讯', '阿里巴巴', '美团', '百度', '京东', '华为', '拼多多', 'MiniMax', '智谱 AI', 'DeepSeek'].includes(company.name),
)
