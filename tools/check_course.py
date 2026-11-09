"""Check course navigation and the shared lesson template without running examples."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def visible_markdown(text):
    """Do not count headings inside sample code fences as lesson structure."""
    lines = []
    fence = None
    for line in text.splitlines():
        stripped = line.lstrip()
        if fence:
            if stripped.startswith(fence):
                fence = None
            continue
        if stripped.startswith(('```', '~~~')):
            fence = stripped[:3]
            continue
        lines.append(line)
    return '\n'.join(lines)


def sections(text):
    visible = visible_markdown(text)
    found = list(re.finditer(r'^## (.+)$', visible, re.M))
    return [(match.group(1), visible[match.end():found[index+1].start() if index+1 < len(found) else len(visible)].strip())
            for index, match in enumerate(found)]


def check_course():
    spec = json.loads((ROOT / 'configs/course.json').read_text(encoding='utf-8'))
    expected = spec['sections']
    chapters = spec['chapters']
    ids = [chapter['id'] for chapter in chapters]
    files = [chapter['file'] for chapter in chapters]
    errors = []
    if spec.get('schema_version') != 2:
        errors.append('Unsupported course schema')
    if len(ids) != len(set(ids)) or len(files) != len(set(files)):
        errors.append('Duplicate chapter ID or file')
    assigned = [ident for stage in spec['stages'] for ident in stage['chapters']]
    if sorted(assigned) != sorted(ids):
        errors.append('Stages must cover every chapter exactly once')
    stage_titles = ['设备接入', '感知', '决策', '执行', '反馈', '部署维护']
    if [stage['title'] for stage in spec['stages']] != stage_titles:
        errors.append('Use the six development stages in the required order')
    if len({stage['id'] for stage in spec['stages']}) != len(spec['stages']):
        errors.append('Duplicate stage ID')
    if len({stage['file'] for stage in spec['stages']}) != len(spec['stages']):
        errors.append('Duplicate stage guide')
    required_sections = ['能力目标', '前置条件', '输入输出与接口', '最小示例', '可修改与扩展点', '验证方法']
    if expected != required_sections:
        errors.append('Use the six shared capability sections')
    stage_for = {ident: stage for stage in spec['stages'] for ident in stage['chapters']}
    for name, route in spec['routes'].items():
        if len(route) != len(set(route)) or any(ident not in ids for ident in route):
            errors.append('Unknown or duplicate chapter in route ' + name)
    actual_files = {path.relative_to(ROOT).as_posix() for path in (ROOT / 'docs/tutorials').glob('[0-9][0-9]-*.md')}
    if actual_files != set(files):
        errors.append('Course catalog does not match the tutorial files')
    template_sections = [name for name, _ in sections((ROOT / 'docs/lesson-template.md').read_text(encoding='utf-8'))]
    if template_sections != expected:
        errors.append('Author template differs from course section contract')
    index_text = (ROOT / 'docs/tutorials/README.md').read_text(encoding='utf-8')
    framework = (ROOT / 'docs/learning-framework.md').read_text(encoding='utf-8')
    home = (ROOT / 'README.md').read_text(encoding='utf-8')
    for stage in spec['stages']:
        if stage['title'] not in framework or stage['title'] not in home:
            errors.append('Stage missing from framework/home: ' + stage['id'])
        guide = (ROOT / stage['file']).resolve()
        if not guide.is_relative_to((ROOT / 'docs/framework').resolve()) or not guide.is_file():
            errors.append('Missing or out-of-scope stage guide: ' + stage['file'])
            continue
        text = guide.read_text(encoding='utf-8')
        parts = sections(text)
        if not text.startswith('# ' + stage['title'] + '\n'):
            errors.append('Stage guide title mismatch: ' + stage['id'])
        if [name for name, _ in parts] != expected or any(not body for _, body in parts):
            errors.append('Stage guide must use all six populated sections: ' + stage['id'])
        else:
            if not re.search(r'^\d+\. ', dict(parts)['最小示例'], re.M):
                errors.append('Stage guide needs an ordered example: ' + stage['id'])
            if '| 提交证据 |' not in dict(parts)['验证方法']:
                errors.append('Stage guide needs evidence criteria: ' + stage['id'])
            for boundary in ('输入', '输出', '错误'):
                if '| ' + boundary + ' |' not in dict(parts)['输入输出与接口']:
                    errors.append('Stage guide missing interface boundary: ' + stage['id'] + '/' + boundary)
        if '](framework/' + guide.name + ')' not in framework:
            errors.append('Framework missing stage guide link: ' + stage['id'])
        if '](docs/framework/' + guide.name + ')' not in home:
            errors.append('Home missing stage guide link: ' + stage['id'])
    actual_guides = {path.relative_to(ROOT).as_posix() for path in (ROOT / 'docs/framework').glob('*.md')}
    if actual_guides != {stage['file'] for stage in spec['stages']}:
        errors.append('Stage guide catalog does not match framework files')
    topics = spec.get('topics', [])
    topic_index = (ROOT / 'docs/topics/README.md').read_text(encoding='utf-8')
    if len({topic['id'] for topic in topics}) != len(topics):
        errors.append('Duplicate topic ID')
    if len({topic['file'] for topic in topics}) != len(topics):
        errors.append('Duplicate topic file')
    stage_ids = {stage['id'] for stage in spec['stages']}
    for topic in topics:
        label = topic['id']
        assigned_stages = topic['stages']
        if (not assigned_stages or len(assigned_stages) != len(set(assigned_stages))
                or any(stage not in stage_ids for stage in assigned_stages)):
            errors.append('Unknown, empty or duplicate topic stage: ' + label)
        path = (ROOT / topic['file']).resolve()
        if not path.is_relative_to((ROOT / 'docs/topics').resolve()) or not path.is_file():
            errors.append('Missing or out-of-scope topic: ' + label)
            continue
        text = path.read_text(encoding='utf-8')
        if not text.startswith('# ' + topic['title'] + '\n'):
            errors.append('Topic title mismatch: ' + label)
        if topic.get('kind') != '扩展设计指南' or '类型：扩展设计指南' not in text:
            errors.append('Topic must identify its design scope: ' + label)
        parts = sections(text)
        if [name for name, _ in parts] != expected or any(not body for _, body in parts):
            errors.append('Topic must use all six populated sections: ' + label)
        else:
            if not re.search(r'^\d+\. ', dict(parts)['最小示例'], re.M):
                errors.append('Topic needs an ordered example: ' + label)
            if '| 提交证据 |' not in dict(parts)['验证方法']:
                errors.append('Topic needs evidence criteria: ' + label)
        if f"[{topic['title']}]({path.name})" not in topic_index:
            errors.append('Topic index missing entry: ' + label)
        if '](README.md)' not in text or '](../learning-framework.md)' not in text:
            errors.append('Topic missing return navigation: ' + label)
    actual_topics = {path.relative_to(ROOT).as_posix() for path in (ROOT / 'docs/topics').glob('*.md')
                     if path.name != 'README.md'}
    if actual_topics != {topic['file'] for topic in topics}:
        errors.append('Topic catalog does not match topic files')
    for index, chapter in enumerate(chapters):
        path = (ROOT / chapter['file']).resolve()
        if not path.is_relative_to((ROOT / 'docs/tutorials').resolve()) or not path.is_file():
            errors.append('Missing or out-of-scope tutorial: ' + chapter['file'])
            continue
        text = path.read_text(encoding='utf-8')
        label = chapter['id']
        heading = f"# 第 {label} 章：{chapter['title']}"
        if text.splitlines()[0] != heading:
            errors.append(label + ': title differs from course catalog')
        parts = sections(text)
        if [name for name, _ in parts] != expected:
            errors.append(label + ': use the six template sections once, in the required order')
            continue
        if any(not body for _, body in parts):
            errors.append(label + ': empty template section')
        conditions = dict((cells[1].strip(), cells[2].strip())
                          for line in dict(parts)['前置条件'].splitlines()
                          if line.startswith('|') and len(cells := line.split('|')) == 4)
        for key in spec['condition_fields']:
            if not conditions.get(key) or conditions[key] in ('待填写', '待补充'):
                errors.append(label + ': missing concrete condition ' + key)
        if conditions.get('学习类型') != chapter['kind']:
            errors.append(label + ': learning type differs from course catalog')
        stage = stage_for.get(label)
        if stage is None or conditions.get('所属环节') != stage['title']:
            errors.append(label + ': stage differs from course catalog')
        for boundary in ('输入', '输出', '错误边界'):
            if '| ' + boundary + ' |' not in dict(parts)['输入输出与接口']:
                errors.append(label + ': missing interface boundary ' + boundary)
        if not re.search(r'^\d+\. ', dict(parts)['最小示例'], re.M):
            errors.append(label + ': practice needs an ordered task')
        if '| 提交证据 |' not in dict(parts)['验证方法']:
            errors.append(label + ': acceptance needs evidence column')
        navigation = dict(parts)['验证方法']
        if '### 下一步与参考' not in navigation:
            errors.append(label + ': missing navigation subsection')
        if '- 上一章：' not in navigation or '- 下一章：' not in navigation:
            errors.append(label + ': missing previous/next navigation')
        for adjacent in (index-1, index+1):
            if 0 <= adjacent < len(chapters) and '](' + Path(chapters[adjacent]['file']).name + ')' not in navigation:
                errors.append(label + ': missing adjacent chapter link')
        if '](../learning-framework.md)' not in navigation:
            errors.append(label + ': missing framework navigation')
        if stage and '](../framework/' + Path(stage['file']).name + ')' not in navigation:
            errors.append(label + ': missing stage guide navigation')
        row = f"| [{label} {chapter['title']}]({Path(chapter['file']).name}) | {chapter['kind']} | {chapter['outcome']} |"
        if row not in index_text:
            errors.append(label + ': tutorial index differs from course catalog')
    return {'chapters_checked': len(chapters), 'stages_checked': len(spec['stages']), 'topics_checked': len(topics),
            'sections_per_chapter': len(expected), 'errors': errors}


def main():
    try:
        report = check_course()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'errors': [str(error)]}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(bool(report['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
