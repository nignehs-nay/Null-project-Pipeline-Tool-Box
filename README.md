# Null Project Pipeline Tool Box

空项目工具箱

## 项目简介

我自己的使用的blender插件，主要是针对自己的需求和习惯，给自己定制的一个插件。
插件的大部分功能可能并不符合其他大部分人的习惯，有很多功能是可以通过快捷键来完成，即便不需要快捷键应该也可以通过常规的方式来完成。
使用插件至少需要Blender-4.2，在Blender-4.2版本下进行开发和测试。
（（因为使用了Ai来进行辅助编写，所以其实哥们目前还不会用git））

## 功能特点

- 在物体模式和姿态模式之间一键切换，提高角色动画制作时的工作效率。
- 添加4种类型的空物体（坐标轴、箭头、立方体、圆形）
- 将选中的摄像机设为活动摄像机
- 用于rigfy骨骼的IK/FK切换工具​，智能识别并切换骨骼的IK/FK状态，自动检测选中的肢体类型（左臂/右臂/左腿/右腿），支持IK→FK和FK→IK的双向切换，动检测当前状态并切换到相反模式
- 角色关键帧插入工具，完整角色关键帧，选中骨骼关键帧
- 添加Human Metarig，Basic Human，生成Rigify绑定
- 创建预览动画，通过工作台渲染器来渲染，渲染完成后自动播放动画，可指定输出路径和文件名，支持MP4、QuickTime、AVI格式
- 在线扩展安装和更新

## 安装与配置

1. 克隆仓库到本地机器：
   ```bash
   git clone https://gitee.com/nignehs-nay/null-project-pipeline-box.git
   ```

2. 进入项目目录：
   ```bash
   cd null-project-pipeline-box
   ```

3. 查看并根据需要修改`.gitignore`文件以适应您的开发环境需求。

4. 阅读`LICENSE`文件了解项目的许可协议。

## 使用说明

该项目主要用于个人的项目，根据我自己的需求来定制，您可以将其作为新项目的起点。只需复制此项目的结构到新的仓库中，并开始添加您自己的代码和功能。

## 贡献指南

我们欢迎贡献！如果您有兴趣改进这个项目，请遵循以下步骤：

1. Fork 仓库
2. 创建一个新的分支 (`git checkout -b feature/new-feature`)
3. 提交您的更改 (`git commit -am 'Add some feature'`)
4. 推送到分支 (`git push origin feature/new-feature`)
5. 创建一个 Pull Request

## 许可证

该项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。