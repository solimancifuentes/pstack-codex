import copy
from pathlib import Path
import unittest

from discover_skills import assess_discovery


class NativeDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path('/tmp/pstack-codex-validation')
        self.plugin_id = 'pstack-codex@personal'
        self.cache = self.root / 'plugins/cache/personal/pstack-codex/0.2.0'
        self.skills = {'data': [{'cwd': str(self.root / 'project'),
                                'skills': [self.skill('alpha'), self.skill('beta')], 'errors': []}]}
        self.plugins = {'marketplaces': [{'name': 'personal', 'plugins': [
            {'id': self.plugin_id, 'name': 'pstack-codex', 'installed': True, 'enabled': True,
             'source': {'type': 'local', 'path': str(self.root / 'marketplace/plugins/pstack-codex')}}]}]}
        self.manifest = {'skills': [{'name': 'alpha'}, {'name': 'beta'}]}

    def skill(self, name, plugin_id=None, root=None):
        return {'name': 'pstack-codex:' + name, 'pluginId': plugin_id or self.plugin_id,
                'path': str((root or self.cache) / 'skills' / name / 'SKILL.md'), 'enabled': True}

    def assess(self, selector='pstack-codex', manifest=None):
        return assess_discovery(self.skills, self.plugins, selector, 2,
                                self.manifest if manifest is None else manifest)

    def test_scratch_directory_name_does_not_claim_system_or_similarly_named_plugins(self):
        self.skills['data'][0]['skills'].extend([
            {'name': 'skill-creator', 'pluginId': None, 'enabled': True,
             'path': str(self.root / 'skills/.system/skill-creator/SKILL.md')},
            self.skill('alpha', plugin_id='pstack-codex-extra@personal')])
        result = self.assess()
        self.assertTrue(result['passed'])
        self.assertEqual([skill['name'] for skill in result['matching_plugin_skills']],
                         ['pstack-codex:alpha', 'pstack-codex:beta'])

    def test_bare_name_requires_one_marketplace_and_full_id_selects_exactly_one(self):
        other = copy.deepcopy(self.plugins['marketplaces'][0]['plugins'][0])
        other['id'] = 'pstack-codex@other'
        self.plugins['marketplaces'].append({'name': 'other', 'plugins': [other]})
        self.skills['data'][0]['skills'].append(self.skill('alpha', plugin_id=other['id']))
        self.assertFalse(self.assess()['passed'])
        result = self.assess(self.plugin_id)
        self.assertTrue(result['passed'])
        self.assertEqual(result['matching_plugin_ids'], [self.plugin_id])

    def test_disabled_skills_do_not_count_as_available(self):
        self.skills['data'][0]['skills'][1]['enabled'] = False
        result = self.assess()
        self.assertFalse(result['passed'])
        self.assertEqual(len(result['matching_plugin_skills']), 1)
        self.assertEqual(result['missing_expected_skills'], ['pstack-codex:beta'])

    def test_repeated_cwd_observations_count_each_identity_once(self):
        self.skills['data'].append(copy.deepcopy(self.skills['data'][0]))
        result = self.assess()
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['matching_plugin_skills']), 2)
        self.assertEqual(result['duplicate_skill_rows'], 2)

    def test_same_identity_at_another_version_path_fails(self):
        self.skills['data'][0]['skills'].append(self.skill('alpha', root=self.cache.parent / '0.1.0'))
        result = self.assess()
        self.assertFalse(result['passed'])
        self.assertEqual(len(result['conflicting_skill_rows']), 1)

    def test_expected_manifest_rejects_equal_count_with_a_stale_skill_name(self):
        result = self.assess(manifest={'skills': [{'name': 'alpha'}, {'name': 'gamma'}]})
        self.assertFalse(result['passed'])
        self.assertEqual(result['missing_expected_skills'], ['pstack-codex:gamma'])
        self.assertEqual(result['unexpected_skills'], ['pstack-codex:beta'])

    def test_parse_errors_belong_only_to_actual_plugin_roots(self):
        unrelated = {'path': str(self.root / 'skills/.system/bad/SKILL.md'), 'message': 'unrelated'}
        sibling = {'path': str(self.cache.with_name('0.2.0-other') / 'skills/bad/SKILL.md'), 'message': 'sibling'}
        self.skills['data'][0]['errors'] = [unrelated, sibling]
        self.assertTrue(self.assess()['passed'])
        owned = {'path': str(self.cache / 'skills/bad/SKILL.md'), 'message': 'invalid frontmatter'}
        self.skills['data'][0]['errors'].append(owned)
        result = self.assess()
        self.assertFalse(result['passed'])
        self.assertEqual(result['matching_parse_errors'], [owned])

    def test_plugin_must_be_installed_and_enabled_in_native_listing(self):
        for state in ('installed', 'enabled'):
            with self.subTest(state=state):
                self.plugins['marketplaces'][0]['plugins'][0][state] = False
                self.assertFalse(self.assess()['passed'])
                self.plugins['marketplaces'][0]['plugins'][0][state] = True

    def test_manifest_rejects_duplicate_expected_names(self):
        with self.assertRaises(ValueError):
            self.assess(manifest={'skills': [{'name': 'alpha'}, {'name': 'alpha'}]})


if __name__ == '__main__':
    unittest.main()
