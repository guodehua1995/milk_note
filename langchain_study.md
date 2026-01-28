# 介绍
langchain1.0干中学的学习笔记,非系统学习,干到哪学到哪。

图api介绍
    https://docs.langchain.com/oss/python/langgraph/graph-api

# Agent
    创建/调用agent

# 记忆存储
langchain的记忆存储分为checkpoints和store两种
checkpoints是指agent的运行状态,可以进行持久化用来快速恢复agent运行。
store是指业务数据记录,可以通过namespace来进行区分,不同namespace可以类比为不同表。
    问题: 如何查询namespace里面的数据呢？查询条件支持哪些？