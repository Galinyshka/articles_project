import logging as logger
from jinja2 import Environment, FileSystemLoader

# Configure logging

def render_template(template_name, **context):
    # Log the context to verify it contains the 'scenes' key
    # logger.debug(context)
    
    env = Environment(loader=FileSystemLoader('/home/galinyshka/code/articles_project/zeroshot'))
    template = env.get_template(template_name)
    
    # Render the template and log the output
    rendered_template = template.render(**context)
    logger.debug(f"Rendered Template: {rendered_template}")
    
    return rendered_template

# Example usage
#if __name__ == "__main__":
#    # Ensure Settings.instructions_path is correctly defined
#    scenes = ["Scene 1", "Scene 2", "Scene 3"]
#    context = {"scenes": scenes}
#    rendered_output = render_template("your_template_name.txt", **context)
#    print(rendered_output)