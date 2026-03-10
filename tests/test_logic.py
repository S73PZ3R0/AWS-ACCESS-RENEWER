import unittest
from aws_access_renewer.core.network import normalize_ip
from aws_access_renewer.core.aws import EC2Service
from aws_access_renewer.core.updater import SSHRuleUpdater

class TestLogic(unittest.TestCase):
    def test_normalize_ipv4(self):
        self.assertEqual(normalize_ip("1.2.3.4"), "1.2.3.4/32")
        self.assertEqual(normalize_ip("1.2.3.4/24"), "1.2.3.4/24")

    def test_normalize_ipv6(self):
        self.assertEqual(normalize_ip("2001:db8::1"), "2001:db8::1/128")
        self.assertEqual(normalize_ip("2001:db8::/32"), "2001:db8::/32")

    def test_instance_name_tag(self):
        instance = {
            "Tags": [
                {"Key": "Name", "Value": "my-instance"},
                {"Key": "Environment", "Value": "prod"}
            ]
        }
        self.assertEqual(EC2Service.instance_name(instance), "my-instance")

    def test_sshrrule_updater_matching(self):
        instance = {
            "InstanceId": "i-123",
            "SecurityGroups": [{"GroupId": "sg-1"}]
        }
        updater = SSHRuleUpdater(instance, [22, 443], "1.1.1.1")
        
        matching_rule_22 = {
            "GroupId": "sg-1",
            "IsEgress": False,
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22
        }
        matching_rule_443 = {
            "GroupId": "sg-1",
            "IsEgress": False,
            "IpProtocol": "tcp",
            "FromPort": 443,
            "ToPort": 443
        }
        non_matching_port = {
            "GroupId": "sg-1",
            "IsEgress": False,
            "IpProtocol": "tcp",
            "FromPort": 80,
            "ToPort": 80
        }
        non_matching_sg = {
            "GroupId": "sg-2",
            "IsEgress": False,
            "IpProtocol": "tcp",
            "FromPort": 22,
            "ToPort": 22
        }
        
        self.assertTrue(updater._is_matching_ssh_rule(matching_rule_22))
        self.assertTrue(updater._is_matching_ssh_rule(matching_rule_443))
        self.assertFalse(updater._is_matching_ssh_rule(non_matching_port))
        self.assertFalse(updater._is_matching_ssh_rule(non_matching_sg))

if __name__ == "__main__":
    unittest.main()
