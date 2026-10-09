const iconRules: Array<{ keywords: string[]; iconName: string }> = [
  { keywords: ['python', '代码', '脚本', 'bash', 'shell'], iconName: 'Code' },
  { keywords: ['逻辑', '开始', '结束', '条件', '分支'], iconName: 'BranchFork2' },
  { keywords: ['数据集', '数据导入', '数据导出', '数据库', 'datax', 'mysql', 'postgres', 'hive'], iconName: 'Database' },
  { keywords: ['模型导入', '模型下载', '模型注册', '模型转换', '模型评估'], iconName: 'CubeShape' },
  { keywords: ['图像', '图片', '视觉', 'image'], iconName: 'Photo' },
  { keywords: ['视频', 'video'], iconName: 'Video' },
  { keywords: ['音频', '语音', 'audio'], iconName: 'Audio' },
  { keywords: ['文本', '自然语言', 'nlp', '大模型', 'llm'], iconName: 'TextDocument' },
  { keywords: ['训练', 'tensorflow', 'pytorch', 'mindspore', '机器学习', '深度学习'], iconName: 'Processing' },
  { keywords: ['服务', '部署', '推理', 'endpoint'], iconName: 'CloudUpload' },
  { keywords: ['spark', 'hadoop', '分布式', 'ray', '加速'], iconName: 'Server' },
  { keywords: ['自定义镜像', '镜像', 'docker', '容器'], iconName: 'CubeShape' },
  { keywords: ['特征', '预处理', '清洗', '异常值', '缺失值'], iconName: 'Processing' },
];

const knownIcons = new Set([
  'Code', 'BranchFork2', 'Database', 'CubeShape', 'Photo', 'Video', 'Audio',
  'TextDocument', 'Processing', 'CloudUpload', 'Server', 'GitGraph', 'BoxAdditionSolid',
  'BuildQueue', 'ImagePixel', 'FileCode', 'FabricFolder', 'Settings',
]);

export const getTemplateIcon = (template: any): string => {
  const configuredIcon = template?.expand?.icon || template?.icon;
  if (typeof configuredIcon === 'string' && knownIcons.has(configuredIcon)) return configuredIcon;
  const searchableText = `${template?.name || ''} ${template?.describe || ''}`.toLowerCase();
  const rule = iconRules.find(({ keywords }) => keywords.some(keyword => searchableText.includes(keyword)));
  return rule?.iconName || 'GitGraph';
};
