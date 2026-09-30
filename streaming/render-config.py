"""Generate and SDK-validate MediaLive request JSON without contacting AWS."""
import argparse
import json
from pathlib import Path
from botocore.session import Session
from botocore.validate import validate_parameters

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bucket', required=True)
parser.add_argument('--role-arn', required=True)
parser.add_argument('--secret-arn', required=True)
parser.add_argument('--input-id', default='REPLACE_AFTER_CREATE_INPUT')
parser.add_argument('--security-group-id', default='REPLACE_AFTER_CREATE_SECURITY_GROUP')
parser.add_argument('--output', default='/evidence')
args = parser.parse_args()

input_request = {
    'Name': 'assessment-hevc-srt', 'Type': 'SRT_LISTENER',
    'InputSecurityGroups': [args.security_group_id], 'RoleArn': args.role_arn,
    'SrtSettings': {'SrtListenerSettings': {
        'Decryption': {'Algorithm': 'AES256', 'PassphraseSecretArn': args.secret_arn},
        'MinimumLatency': 1000
    }}
}
channel_request = {
    'Name': 'assessment-hevc-archive', 'ChannelClass': 'SINGLE_PIPELINE',
    'RoleArn': args.role_arn,
    'InputSpecification': {'Codec': 'HEVC', 'MaximumBitrate': 'MAX_20_MBPS', 'Resolution': 'HD'},
    'InputAttachments': [{'InputId': args.input_id, 'InputAttachmentName': 'hevc-source',
        'InputSettings': {'AudioSelectors': [{'Name': 'audio-default'}]}}],
    'Destinations': [{'Id': 'archive', 'Settings': [{'Url': f's3://{args.bucket}/recordings/broadcast'}]}],
    'EncoderSettings': {
        'TimecodeConfig': {'Source': 'SYSTEMCLOCK'},
        'AudioDescriptions': [{'Name': 'aac-192', 'AudioSelectorName': 'audio-default',
            'CodecSettings': {'AacSettings': {'Bitrate': 192000, 'CodingMode': 'CODING_MODE_2_0',
                'SampleRate': 48000, 'Profile': 'LC', 'RateControlMode': 'CBR', 'Spec': 'MPEG4'}}}],
        'VideoDescriptions': [{'Name': 'hevc-hd', 'Width': 1920, 'Height': 1080,
            'CodecSettings': {'H265Settings': {'Bitrate': 12000000,
                'FramerateNumerator': 25, 'FramerateDenominator': 1,
                'RateControlMode': 'CBR', 'GopSize': 2, 'GopSizeUnits': 'SECONDS',
                'Profile': 'MAIN', 'Tier': 'MAIN'}}}],
        'OutputGroups': [{'Name': 'S3 TS archive',
            'OutputGroupSettings': {'ArchiveGroupSettings': {
                'Destination': {'DestinationRefId': 'archive'}, 'RolloverInterval': 60}},
            'Outputs': [{'OutputName': 'hevc-ts', 'VideoDescriptionName': 'hevc-hd',
                'AudioDescriptionNames': ['aac-192'],
                'OutputSettings': {'ArchiveOutputSettings': {
                    'NameModifier': '_hd', 'Extension': 'ts',
                    'ContainerSettings': {'M2tsSettings': {}}}}}]}]
    }
}
service = Session().get_service_model('medialive')
output = Path(args.output)
output.mkdir(parents=True, exist_ok=True)
for operation, data, filename in [('CreateInput', input_request, 'input.json'),
                                  ('CreateChannel', channel_request, 'channel.json')]:
    validate_parameters(data, service.operation_model(operation).input_shape)
    (output / filename).write_text(json.dumps(data, indent=2) + '\n')
    print(f'{operation}: SDK request schema PASS ({filename}); no AWS resources created')
