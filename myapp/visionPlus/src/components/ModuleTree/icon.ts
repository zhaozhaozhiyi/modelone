const iconRules: Array<{ keywords: string[]; iconName: string }> = [
  { keywords: ['python', '代码', '脚本', 'bash', 'shell'], iconName: 'Code' },
  { keywords: ['逻辑', '开始', '结束', '条件', '分支'], iconName: 'BranchFork2' },
  { keywords: ['数据集', '数据导入', '数据导出', '数据库', 'datax', 'mysql', 'postgres', 'hive'], iconName: 'Database' },
  { keywords: ['模型', '训练', 'tensorflow', 'pytorch', '机器学习', '深度学习'], iconName: 'Processing' },
  { keywords: ['图像', '图片', '视觉', 'image'], iconName: 'Photo' },
  { keywords: ['视频', 'video'], iconName: 'Video' },
  { keywords: ['音频', '语音', 'audio'], iconName: 'Audio' },
  { keywords: ['文本', '自然语言', 'nlp', '大模型', 'llm'], iconName: 'TextDocument' },
  { keywords: ['服务', '部署', '推理'], iconName: 'CloudUpload' },
  { keywords: ['spark', 'hadoop', '分布式', 'ray', '加速'], iconName: 'Server' },
  { keywords: ['镜像', 'docker', '容器'], iconName: 'CubeShape' },
  { keywords: ['特征', '预处理', '清洗', '异常值', '缺失值'], iconName: 'Processing' },
];
const knownIcons = new Set(['Code', 'BranchFork2', 'Database', 'CubeShape', 'Photo', 'Video', 'Audio', 'TextDocument', 'Processing', 'CloudUpload', 'Server', 'GitGraph']);
export const getTemplateIcon = (template: any): string => {
  const configuredIcon = template?.expand?.icon || template?.icon;
  if (typeof configuredIcon === 'string' && knownIcons.has(configuredIcon)) return configuredIcon;
  const text = `${template?.name || ''} ${template?.describe || ''}`.toLowerCase();
  return iconRules.find(({ keywords }) => keywords.some(keyword => text.includes(keyword)))?.iconName || 'GitGraph';
};
