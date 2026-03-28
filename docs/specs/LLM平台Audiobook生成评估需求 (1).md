# LLM平台Audiobook生成评估需求

<!--
status: active
date: 2026-03-28
tags: [audiobook, evaluation, tts, annotation]
-->

## 1. 需求背景与目标

*   背景：目前有声书音频生成的标注及抽卡（重新生成）工作依赖Excel线下流转。标注员需要手动核对文本、播放音频、填写多项修改意见并粘贴新音频。这种方式存在效率低、易出错、数据难以结构化统计、且无法限制必填逻辑等问题。
    
*   目标：将此业务流程迁移至现有的标注平台。通过系统化的前端交互（特别是条件联动展示），提高标注效率，规范数据产出格式，并为后续的质检提供标准化的线上工作台。
    

## 2. 用户角色

*   标注员：执行主要的试听、判定、文本修改及新音频上传工作。
    
*   质检员：对标注员提交为“已完成”的任务进行抽查和复核（本期需求重点在标注端，但最好预留质检状态）。
    

## 3. 核心业务流程 

1.  进入任务，系统自动加载当前切片的原始文本和初始生成的音频。
    
2.  标注员点击播放音频，对比文本进行核查。
    
3.  核心判定节点：选择音频是否可用？
    
    *   分支 A (可用)：勾选【可用】 -> 无需填写其他信息 -> 点击【提交/下一题】 -> 任务状态变更为“已完成”。
        
    *   分支 B (不可用)：勾选【不可用】 -> 系统向下展开扩展表单 -> 标注员选择Badcase分类 -> 根据需要修改原始文本 -> 上传抽卡后的最佳音频 or 调用TTS接口一键生成 -> 填写备注 -> 点击【提交/下一题】 -> 任务状态变更为“已完成”。
        

## 4. 功能详细说明与字段映射

原始线下表格标注示例图：

[https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK3m7j6xcOkBGK6XJkb4Mw9r?utm\_scene=person\_space&iframeQuery=sheet\_range%3Dkgqie6hm\_0\_0\_1\_1](https://alidocs.dingtalk.com/i/nodes/lyQod3RxJK3m7j6xcOkBGK6XJkb4Mw9r?utm_scene=person_space&iframeQuery=sheet_range%3Dkgqie6hm_0_0_1_1)

![截屏2026-03-05 18.48.13.png](https://zyb-saas-info-document-alidocs.oss-cn-beijing.aliyuncs.com/res/5adV21ZWObaDpXeb/img/1c96d6ce-4f22-4fbf-bb50-813a8e3d5658.png?Expires=1774666948&OSSAccessKeyId=LTAI5t8KEoEQ2vTqsvMNnXDw&Signature=e0NjnGyyDNUWUkrnP3MaCsIXgfc%3D)

|  Excel 列名  |  平台对应模块  |  控件类型与交互逻辑  |  是否必填  |
| --- | --- | --- | --- |
|  章节名称 / 切片片段  |  左侧列表 / 顶部Task ID  |  纯文本展示（如：`Chapter 1 - fragment_17`）  |  \-  |
|  原始音频  |  中部：前置信息  |  音频播放器组件 (支持播放、暂停、进度条、倍速)  |  \-  |
|  文本内容 (原始)  |  中部：前置信息  |  文本展示框 (需支持长文本滚动)  |  \-  |
|  初始音频是否可用  |  右侧：标注作答  |  单选Button：\[可用\] / \[不可用\] (此项为后续表单的触控开关)  |  是  |
|  badcase 分类  |  右侧：标注作答 (不可用时展示)  |  下拉问题项多选框 (如：稳定性问题、副语言问题等)  |  若不可用则必填  |
|  修改后内容  |  右侧：标注作答 (不可用时展示)  |  文本输入框 (最好默认带入原始文本，供用户在此基础上修改)  |  否(视情况)  |
|  抽卡后最佳音频  |  右侧：标注作答 (不可用时展示)  |  文件上传组件或内置TTS接口  |  若不可用则必填  |
|  备注  |  右侧：标注作答 (不可用时展示)  |  文本输入框  |  否  |

## 5. 原型设计与期望前端页面 Demo

### 场景一：初始加载 / 标注为【可用】的状态

_当用户认为音频没有问题时，界面保持极简，提高吞吐量。_

期望效果图

![audio_evaluation_ui.png](https://zyb-saas-info-document-alidocs.oss-cn-beijing.aliyuncs.com/res/5adV21ZWObaDpXeb/img/6b710a19-ab64-4161-8410-0b56d43cc74c.png?Expires=1774666948&OSSAccessKeyId=LTAI5t8KEoEQ2vTqsvMNnXDw&Signature=NetYd7K6U%2FkcaIvO%2B9dCeEgN0s8%3D)

### 场景二：标注为【不可用】的状态

_当用户点击“不可用”时，下方会展开需要填写的修改信息和上传组件。_

方式一：同原始评估方式，在抽卡平台生成新音频后，用户将音频保存在本地，然后上传至平台

期望效果图

![audio_evaluation_ui_v2.png](https://zyb-saas-info-document-alidocs.oss-cn-beijing.aliyuncs.com/res/5adV21ZWObaDpXeb/img/2c1f1459-13cf-4d6f-8947-c791329469f3.png?Expires=1774666948&OSSAccessKeyId=LTAI5t8KEoEQ2vTqsvMNnXDw&Signature=npvB%2FDWefkmo3mVAUZDC8xfOIgw%3D)

方式二：无需线下生成再上传，而是直接在页面内嵌入TTS接口，用户改完文本后一键生成音频、试听、抽卡选择。

期望效果图

![audio_evaluation_ui_v3_tts.png](https://zyb-saas-info-document-alidocs.oss-cn-beijing.aliyuncs.com/res/5adV21ZWObaDpXeb/img/e5f00d23-9a05-4301-beab-08e75af841af.png?Expires=1774666948&OSSAccessKeyId=LTAI5t8KEoEQ2vTqsvMNnXDw&Signature=VFpeo6dNHwT6Tzub2MxsF7%2FTNeM%3D)

## 6. 关键交互说明

1.  数据带入：在标注员选择“不可用”展开【修改后文本内容】输入框时，最好将左侧的“原始文本”直接带入填充到输入框中。因为标注员通常只是微调（比如改个别错别字），如果让他们重新复制粘贴会极大降低效率。
    
2.  音频上传验证：【抽卡后最佳音频】建议在下方渲染一个Mini播放器供标注人员自己复核检查。
    
3.  表单校验：只有在选择了“不可用”时，Badcase分类和新音频才是“必填”状态。如果选择“可用”，提交时不校验下方隐藏的字段。