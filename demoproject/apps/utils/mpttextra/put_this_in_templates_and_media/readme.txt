
TREE_EDITOR.HTML

this template file was originally part of feincms

it is needed for displaying the tree properly in the admin

it needs to be put under your /templates directory, or in /templates/admin
(you could customize this position by looking at the source code of feincms_tree_editor.py)


FEINCMS MEDIA

this dir should go in the media directory

A setting needs to be added too:

# settings for FEINCMS media used by the admin-mptt tree visualizer...
MPTTEXTRA_ADMIN_MEDIA = '/static/feincms/'