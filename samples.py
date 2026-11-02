"""Fixed, labelled fixtures. These do not analyse arbitrary user submissions."""
from models import Brief, ModelAssessment

def risk(title, category, likelihood, impact, evidence, rationale, mitigation, signal):
    return dict(title=title, category=category, likelihood=likelihood, impact=impact,
                evidence=evidence, rationale=rationale, mitigation=mitigation, monitoring_signal=signal)

SAMPLES = {
    'migration': {
        'name': 'Cloud migration',
        'brief': dict(title='Move core services to a lower-cost cloud', category='Operations', owner='Platform team', appetite='Balanced',
            decision='Migrate all core services to a lower-cost cloud provider within 30 days. Retire the current environment immediately after cutover.',
            constraints='No additional engineers. No rollback environment is planned. Existing customer uptime commitments remain in place.'),
        'assessment': dict(executive_summary='The proposed migration combines a short delivery window with an irreversible cutover. Establish a tested rollback path and a staged migration before committing to the shutdown. The intended savings need to be assessed alongside migration and resilience costs.',
            risks=[risk('Cutover failure without recovery path', 'Operations', 4, 5, 'No rollback environment is planned.', 'An unsuccessful cutover could interrupt service without a ready route back to the current environment.', 'Keep the existing environment available until rollback and recovery drills pass.', 'Error rate, availability and successful rollback rehearsal'),
                   risk('Delivery capacity is overcommitted', 'Delivery', 4, 4, 'No additional engineers.', 'Migration work competes with ongoing operations and can leave less time for testing.', 'Stage the migration by service and reserve engineering capacity for incident response.', 'Migration milestones and unplanned on-call hours'),
                   risk('Savings omit transition costs', 'Financial', 3, 3, '', 'Parallel running, data transfer and engineering time may reduce the proposed savings.', 'Prepare a total-cost comparison including transition and recovery capacity.', 'Migration spend versus approved transition budget')],
            assumptions=['Core services support customer-facing workloads.', 'Recovery objectives have not yet been validated for the new provider.'],
            open_questions=['What outage duration is acceptable under customer commitments?', 'Who can authorise rollback, and how quickly?'],
            next_steps=['Run a rollback rehearsal before scheduling cutover.', 'Pilot one low-criticality service.', 'Review total costs and agree explicit go/no-go criteria.'],
            outlook=dict(best_case='A staged migration meets recovery criteria and reduces recurring infrastructure costs.', base_case='Additional testing and parallel running extend the timeline and reduce early savings.', worst_case='A cutover incident interrupts service while the previous environment is unavailable.'))},
    'launch': {
        'name': 'Product release',
        'brief': dict(title='Launch the new portal ahead of the campaign', category='Delivery', owner='Product team', appetite='Balanced',
            decision='Launch a new customer portal in three weeks. Limit pre-release QA to smoke tests and increase campaign traffic at launch.',
            constraints='The portal includes account updates. Support coverage is unchanged. A feature flag and rollback deployment are available.'),
        'assessment': dict(executive_summary='The release has recovery options, but limited testing and an immediate traffic increase leave material reliability and account-change risks. Expand the test scope for sensitive paths and ramp traffic gradually before the campaign reaches full scale.',
            risks=[risk('Account-change defects reach customers', 'Security', 3, 5, 'The portal includes account updates.', 'Smoke testing alone may miss access-control and account-update edge cases.', 'Test authorisation boundaries and account-update paths before enabling the feature.', 'Failed account updates and access-control test results'),
                   risk('Campaign load exceeds tested capacity', 'Operations', 3, 4, 'increase campaign traffic at launch.', 'A rapid traffic increase may uncover capacity limits after release.', 'Run a representative load test and increase traffic in controlled stages.', 'Latency, error rate and resource saturation'),
                   risk('Support demand exceeds coverage', 'Reputation', 3, 3, 'Support coverage is unchanged.', 'New customer workflows may create more support demand during launch.', 'Prepare support guidance and assign launch escalation ownership.', 'Ticket inflow and unresolved launch issues')],
            assumptions=['The feature flag can disable the portal without disrupting existing account access.'],
            open_questions=['Which account-update cases have been tested?', 'What metrics automatically trigger rollback?'],
            next_steps=['Complete sensitive-path and authorisation tests.', 'Agree a staged rollout and rollback thresholds.', 'Brief support on expected launch questions.'],
            outlook=dict(best_case='A limited rollout validates key paths and traffic increases without material incidents.', base_case='Early feedback identifies fixes before full campaign traffic is enabled.', worst_case='Sensitive workflow defects and increased traffic produce customer-impacting incidents.'))},
    'docs': {
        'name': 'Internal knowledge base',
        'brief': dict(title='Pilot an internal documentation refresh', category='Operations', owner='Enablement team', appetite='Cautious',
            decision='Pilot a refreshed internal documentation portal with ten volunteers for two weeks. Keep the existing portal available throughout the pilot.',
            constraints='Only existing non-sensitive documentation is included. Content owners review each migrated page. No customer systems are changed.'),
        'assessment': dict(executive_summary='This is a contained, reversible pilot with a limited audience. Focus review on content ownership, access settings and feedback collection. A wider rollout should depend on the pilot evidence rather than assumptions about adoption.',
            risks=[risk('Migrated guidance becomes inconsistent', 'Operations', 2, 3, 'Content owners review each migrated page.', 'Copies of guidance can drift if the team does not identify the authoritative version.', 'Mark one authoritative source and assign a content owner for every page.', 'Broken links and conflicting guidance reports'),
                   risk('Pilot feedback does not represent wider needs', 'Delivery', 2, 2, 'ten volunteers', 'A small volunteer group may not represent all documentation users.', 'Include volunteers from different functions and record unresolved use cases.', 'Feedback coverage across functions')],
            assumptions=['The pilot uses existing internal access controls.'],
            open_questions=['Who owns the final decision about retiring the old portal?'],
            next_steps=['Confirm access settings before inviting volunteers.', 'Collect task-based feedback at the end of each week.', 'Review pilot results before deciding on wider adoption.'],
            outlook=dict(best_case='The pilot improves findability and provides evidence for a wider rollout.', base_case='Feedback identifies content gaps that are resolved before expansion.', worst_case='Inconsistent guidance reduces trust and the team returns to the existing portal.'))}
}

def get_sample(sample_id):
    item = SAMPLES[sample_id]
    return Brief.model_validate(item['brief']), ModelAssessment.model_validate(item['assessment'])
