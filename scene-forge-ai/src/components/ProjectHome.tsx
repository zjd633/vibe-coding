import { Clapperboard, Clock3, FolderKanban, Plus, Sparkles } from 'lucide-react'

interface ProjectHomeProps {
  onOpenProject: () => void
}

const projects = [
  {
    id: 'garden',
    name: '庭院漫剧',
    description: '古风角色、VR360 场景与四格分镜',
    updatedAt: '刚刚更新',
    nodes: 6,
  },
  {
    id: 'dialogue',
    name: '双人对话练习',
    description: '用于快速试镜和人物站位',
    updatedAt: '2 天前',
    nodes: 4,
  },
]

export default function ProjectHome({ onOpenProject }: ProjectHomeProps) {
  return (
    <main id="main-content" className="project-page">
      <header className="project-header">
        <div className="brand-lockup" aria-label="SceneForge AI">
          <span className="brand-mark" aria-hidden="true">
            <Sparkles size={20} />
          </span>
          <span>SceneForge</span>
          <span className="brand-badge">AI</span>
        </div>
        <button className="primary-button" type="button" onClick={onOpenProject}>
          <Plus size={18} aria-hidden="true" />
          新建项目
        </button>
      </header>

      <section className="project-content" aria-labelledby="projects-heading">
        <div className="section-heading">
          <div>
            <p className="eyebrow">WORKSPACE</p>
            <h1 id="projects-heading">项目管理</h1>
            <p>从一个画布组织人物、场景、3D 走位和连续分镜。</p>
          </div>
          <div className="project-stat" aria-label="项目概览">
            <FolderKanban size={20} aria-hidden="true" />
            <span>2 个本地项目</span>
          </div>
        </div>

        <div className="project-grid">
          {projects.map((project, index) => (
            <article className="project-card" key={project.id}>
              <div className={`project-art project-art-${index + 1}`} aria-hidden="true">
                <div className="project-art-grid" />
                <Clapperboard size={30} />
              </div>
              <div className="project-card-body">
                <div>
                  <h2>{project.name}</h2>
                  <p>{project.description}</p>
                </div>
                <div className="project-meta">
                  <span>
                    <Clock3 size={14} aria-hidden="true" /> {project.updatedAt}
                  </span>
                  <span>{project.nodes} 个节点</span>
                </div>
                <button
                  className="secondary-button project-open-button"
                  type="button"
                  aria-label={`打开项目 ${project.name}`}
                  onClick={onOpenProject}
                >
                  打开画布
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </main>
  )
}
