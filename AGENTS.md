本项目严格遵循 superpowers 敏捷开发方法论。

绝对禁令：严禁未经设计直接写代码，必须严格执行 brainstorming → using-git-worktrees → writing-plans → test-driven-development → code-review → finish-branch 的生命周期闭环。

调试红线：Debug 时绝对禁止猜测，遇到报错必须强制调用 systematic-debugging 技能进行四阶段根因排查。

技能触发：所有的技能调用必须通过内置的 Skill 工具（如 Skill(name=“brainstorming”) ）真实执行，严禁仅在对话中口头敷衍或解释。

认知破局：遇到架构冲突、无法定位的死 Bug 或解题卡壳，必须主动使用 problem-solving 类技能（如 when-stuck ）来打破僵局。

readme.md文件描述了项目的主要功能和架构，包括后端、前端、数据库等。

重新启动后端：docker-compose up -d --build backend

重新启动前端：docker-compose up -d --build frontend
