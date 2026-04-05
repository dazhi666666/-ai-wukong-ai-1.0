import { useState } from 'react'
import { DashboardIcon, GuideIcon, ChatIconLarge, WorkflowIcon, SettingsIcon, SystemIcon, ChevronIcon, DatabaseIcon, LogIcon, LogoIcon, UserIcon, CollapseIcon } from './Icons'

function Sidebar({ activeTab, onTabChange }) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [systemExpanded, setSystemExpanded] = useState(true)

  const menuItems = [
    { id: 'dashboard', label: '仪表板', icon: DashboardIcon },
    { id: 'guide', label: '使用指南', icon: GuideIcon },
    { id: 'chat', label: '对话', icon: ChatIconLarge },
    { id: 'workflow', label: '工作流', icon: WorkflowIcon },
    {
      id: 'system',
      label: '系统设置',
      icon: SystemIcon,
      hasChildren: true,
      children: [
        { id: 'logs', label: '日志', icon: LogIcon },
        { id: 'database', label: '数据库', icon: DatabaseIcon },
        { id: 'model', label: '模型配置', icon: SettingsIcon },
      ]
    },
  ]

  const handleItemClick = (id) => {
    onTabChange(id)
  }

  const isChildActive = (children) => {
    return children?.some(child => child.id === activeTab)
  }

  return (
    <aside className={`sidebar ${isCollapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo-container">
          <div className="logo-icon">
            <LogoIcon />
          </div>
          <div className="logo-text">
            <span className="logo-title">LLM Trading</span>
            <span className="logo-subtitle">大模型量化交易平台</span>
          </div>
        </div>
        <button 
          className="collapse-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? '展开菜单' : '收起菜单'}
        >
          <CollapseIcon isCollapsed={isCollapsed} />
        </button>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <div key={item.id} className="nav-item-wrapper">
            <button
              className={`nav-item ${activeTab === item.id || (item.children && isChildActive(item.children)) ? 'nav-item-active' : ''}`}
              onClick={() => {
                if (item.hasChildren) {
                  setSystemExpanded(!systemExpanded)
                } else {
                  handleItemClick(item.id)
                }
              }}
              title={isCollapsed ? item.label : ''}
            >
              <span className="nav-item-indicator"></span>
              <span className="nav-item-icon">
                <item.icon />
              </span>
              <span className="nav-item-label">{item.label}</span>
              {item.hasChildren && (
                <span className={`nav-expand-icon ${systemExpanded ? 'expanded' : ''}`}>
                  <ChevronIcon />
                </span>
              )}
            </button>
            {item.hasChildren && systemExpanded && !isCollapsed && (
              <div className="nav-children">
                {item.children.map((child) => (
                  <button
                    key={child.id}
                    className={`nav-item nav-child-item ${activeTab === child.id ? 'nav-item-active' : ''}`}
                    onClick={() => handleItemClick(child.id)}
                  >
                    <span className="nav-item-indicator"></span>
                    <span className="nav-item-icon">
                      <child.icon />
                    </span>
                    <span className="nav-item-label">{child.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-profile">
          <div className="user-avatar">
            <UserIcon />
          </div>
          <div className="user-info">
            <span className="user-name">管理员用户</span>
            <span className="user-role">系统管理员</span>
          </div>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
