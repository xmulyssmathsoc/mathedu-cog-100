# Dataset Card · MathEdu-Cog 100 v1.1

## 定位 / Intended Use

这是一份数学教育 AI 的**合成种子数据集**，用于结构化标注研究、数据管线与教学策略原型测试。它不构成经过实证验证的学生认知诊断基准，不提供真实学生表现分布，不应被用于对个人学习能力作高风险判断。

## 规模 / Composition

| 类别 | 数量 |
|---|---:|
| 独立核心数学题目 | 100 |
| 详细合成错误案例 | 30（分别链接 30 道母题） |
| 数学概念节点 | 80 |
| 核心规范记录 | 2,081 |
| 全部结构化记录 | 2,111 |
| 数学领域 | 10 |
| 难度等级 | 5（对应学段内相对难度，未用真实人群校准） |

学段覆盖初中、高中、大学基础课程。题目经过有意挑选，**不代表任何学段或地区的真实错误率与题目分布**。

## 数据来源 / Provenance

- 题目、参考答案、错误模式、诊断题与对话：由 GPT-6 在项目对话内构造，并由脚本整理为标准化数据。
- 早期弱模型运行次数：0。
- 真实学生观察记录：0。
- 独立教师或学生实证审定：0。
- 学习结果：不提供已验证的教学效果。

来源元数据详见 `canonical_records.jsonl` 的 `provenance` 记录及 30 例的逐条元数据。

## 核心模式 / Schema

结构化规范包含 `concept`、`item`、`solution`、`error_pattern`、`cognitive_hypothesis`、`diagnostic_probe`、`student_observation`、`cognitive_inference`、`teaching_intervention`、`teaching_session`、`teaching_preference`、`learning_outcome`、`provenance`，以及扩展的 `error_cases`。

规范文件：`schema/record.schema.json` 和 `schema/error_case.schema.json`。

## 质量保证 / Validation

- 100 道题各具有一项定向数学检查；30 个深入错误案例各具有定向检查。
- 数据模式、外键与训练视图隔离经过程序化检查。
- 这些检查**不等同于完整定理证明审定、学生心理测量或教学因果实验**。
- 跨题族的训练、验证、合成测试按 70/15/15 划分。

详情：`reports/quality_report.json`、`reports/30道错误案例质量报告.md`。

## 风险与适用限制 / Known Risks

- AI 构造的错误路径可能不像真实学生；不存在基于真人的发生率估计。
- 同一生成模型可能重复固定教学脚手架，降低语言与策略多样性。
- 在真实学生群体上使用时，需先进行伦理、隐私、分布及性能审核。
- 随机划分的合成测试只能验证生成管线，不可用来声称教育效果。
- 不建议将本数据单独用作真实教育系统的部署依据。

## 联系 / Contact

XMU LYS² MathSoc · xmulyssmathsoc@proton.me
