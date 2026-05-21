class PromptManager:
    """
    提示词模板管理器。

    支持通过 set_template() 动态切换模板，format_prompt()
    使用关键字参数填充模板占位符。
    """

    def __init__(self, template: str = None):
        """
        初始化 PromptManager。

        :param template: 自定义模板字符串，不传则使用默认模板。
                         模板中使用 {key} 作为占位符。
        """
        self.template = template or ""

    def set_template(self, template: str):
        """
        设置提示词模板。

        :param template: 新的模板字符串，使用 {key} 格式的占位符
        """
        self.template = template

    def format_prompt(self, **kwargs) -> str:
        """
        使用给定参数格式化提示词模板。

        :param kwargs: 关键字参数，替换模板中的 {key} 占位符
        :return: 格式化后的完整提示字符串
        """
        return self.template.format(**kwargs)
