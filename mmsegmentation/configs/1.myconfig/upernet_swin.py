# 참조 : upernet_swin_base_patch4_window7_512x512_160k_ade20k_pretrain_224x224_22K.py

_base_ = [
    './models/upernet_swin.py', './datasets/ade20k.py',
    './runtime/default_runtime.py', './schedules/schedule_160k.py'
]

model = dict(
    pretrained='pretrain/swin_base_patch4_window7_224_22k_1.pth',
    backbone=dict(
        embed_dims=128,
        depths=[2, 2, 18, 2],
        num_heads=[4, 8, 16, 32],
        window_size=7,
        use_abs_pos_embed=False,
        drop_path_rate=0.3,
        patch_norm=True),
    decode_head=dict(in_channels=[128, 256, 512, 1024], num_classes=11),
    auxiliary_head=dict(in_channels=512, num_classes=11))

# AdamW optimizer, no weight decay for position embedding & layer norm
# in backbone
optimizer = dict(
    _delete_=True,
    type='AdamW',
    lr=0.00006,
    betas=(0.9, 0.999),
    weight_decay=0.01,
    paramwise_cfg=dict(
        custom_keys={
            'absolute_pos_embed': dict(decay_mult=0.),
            'relative_position_bias_table': dict(decay_mult=0.),
            'norm': dict(decay_mult=0.)
        }))

lr_config = dict(
    _delete_=True,
    policy='poly',
    warmup='linear',
    warmup_iters=1500,
    warmup_ratio=1e-5,
    power=1.0,
    min_lr=0.0,
    by_epoch=False)

# lr_config = dict(
#     _delete_=True,
#     policy='CosineAnnealing',
#     warmup='linear',
#     warmup_iters=10000,
#     warmup_ratio=1.0 / 10,
#     min_lr_ratio=1e-5)