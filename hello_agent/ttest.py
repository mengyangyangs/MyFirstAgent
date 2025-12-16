""" 完整的Agentic RL训练流程
从数据准备到模型部署的端到端示例
 """

from sys import monitoring
from hello_agents.tools import RLTrainingTool
import json
from datetime import datetime

class AgenticRLPipeline:
    """ Agentic RL 训练流水线 """
    def __init__(self,config_path="config.json"):
        """ 初始化流水线 
        Args:
            config_path:配置文件路径
    
        """
        self.rl_tool = RLTrainingTool()
        self.config = self.load_config(config_path)
        self.results = {}

    def load_config(self,config_path):
        """ 加载配置文件 """
        with open(config_path,"r") as f:
            return json.load(f)

    def log(self,message):
        """ 记录日志 """
        timestamp = datetime.now().strftime(" %Y-%m-%d %H:%M:%S ")
        print(f"[{timestamp}] {message}")

    def stage1_prepare_data(self):
        """ 阶段1：数据准备 """
        self.log("=" * 50)
        self.log("阶段1：数据准备")
        self.log("=" * 50)

        # 加载并检查数据集
        result = self.rl_tool.run({
            "action":"load_dataset",
            "format":"sft",
            "max_samples":self.config["data"]["max_samples"]
        })

        # 解析JSON结果
        dataset_info = json.loads(result)
        self.log(f"数据集加载完成")
        self.log(f" - 样本数：{dataset_info["dataset_size"]}")
        self.log(f" - 格式：{dataset_info["format"]}")
        self.log(f" - 数据列：{dataset_info["sample_keys"]}")

        self.results["data"] = dataset_info

        return dataset_info

    def stage2_sft_training(self):
        """ 阶段2:SFT 训练"""
        self.log("\n" + "=" * 50)
        self.log("阶段2: SFT训练")
        self.log("=" * 50)

        sft_config = self.config["sft"]

        result = self.rl_tool.run({
            "action":"train",
            "algorithm":"sft",
            "model_name":self.config["model"]["base_model"],
            "output_dir":sft_config["output_dir"],
            "max_samples":self.config["data"]["max_samples"],
            "num_epochs":sft_config["num_epochs"],
            "batch_size":sft_config["batch_size"],
            "use_lora":True,
        # 训练监控设置
            "use_wandb":self.config.get("monitoring",{}).get("use_wandb",False),
            "use_tensorboard":self.config.get("monitoring",{}).get("use_tensorboard",True),
            "wandb_project":self.config.get("monitoring",{}).get("wandb_project",None)
        })

        result_data = json.loads(result)

        self.log(f"✓ SFT训练完成")
        self.log(f"  - 模型路径: {result_data['output_dir']}")
        self.log(f"  - 状态: {result_data['status']}")

        self.results["sft_training"] = result_data

        return result_data["output_dir"]
    
    def stage3_sft_evaluation(self,model_path):
        """ 阶段3:SFT评估 """
        self.log("\n" + "=" * 50)
        self.log("阶段3: SFT评估")
        self.log("=" * 50)

        

