function interactive_surface_viewer(subject_id, roi)
% INTERACTIVE_SURFACE_VIEWER - 3D brain surface viewer with ROI and functional overlays
%
% Interactive 3D visualization of brain surface data with ROI masks and
% functional activation overlays. Supports rotation, zooming, and view cycling.
%
% Usage:
%   interactive_surface_viewer('sub-08', 'V2')
%
% Inputs:
%   subject_id - Subject identifier (e.g., 'sub-08')
%   roi        - ROI name (V1, V2, V3, hV4)
%
% Requirements:
%   - GIFTI toolbox (from SPM or FieldTrip)
%   - Pre-prepared surface data (.mat files from prepare_matlab_surface_data.py)
%
% Data structure:
%   - freesurfer_surfaces/fsaverage5/lh.inflated.gii: Surface mesh
%   - surface_labels/{subject}/{roi}_lh_label.mat: ROI binary mask
%   - surface_data/{subject}/{roi}_rms.mat: Functional activation values
%
% Author: Generated for colorBlind_analysis project
% Date: 2026-02-22

% Configuration
base_dir = '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis';

fprintf('\n========================================\n');
fprintf('Interactive Surface Viewer\n');
fprintf('Subject: %s | ROI: %s\n', subject_id, roi);
fprintf('========================================\n\n');

% =========================================================================
% Load Surface Geometry
% =========================================================================
fprintf('Loading fsaverage5 inflated surface...\n');
gifti_path = fullfile(base_dir, 'freesurfer_surfaces', 'fsaverage5', 'lh.inflated.gii');

if ~exist(gifti_path, 'file')
    error(['Surface not found: %s\n\n' ...
           'Please download fsaverage5 surfaces from FreeSurfer and convert to GIFTI.\n' ...
           'Or run: prepare_matlab_surface_data.py --export-surfaces'], ...
           gifti_path);
end

g = gifti(gifti_path);
V = g.vertices;  % Nx3 coordinates
F = g.faces;     % Mx3 triangles
fprintf('  Vertices: %d | Faces: %d\n', size(V, 1), size(F, 1));

% =========================================================================
% Load ROI Label
% =========================================================================
fprintf('Loading ROI mask...\n');
roi_label_path = fullfile(base_dir, 'surface_labels', subject_id, ...
                          sprintf('%s_lh_label.mat', roi));

if ~exist(roi_label_path, 'file')
    error(['ROI label not found: %s\n\n' ...
           'Run: python prepare_matlab_surface_data.py --subject %s --roi %s'], ...
           roi_label_path, subject_id, roi);
end

load(roi_label_path, 'roi_label');  % Nx1 logical
fprintf('  ROI vertices: %d (%.1f%%)\n', sum(roi_label), 100*mean(roi_label));

% =========================================================================
% Load Functional Data
% =========================================================================
fprintf('Loading functional activation...\n');
func_path = fullfile(base_dir, 'surface_data', subject_id, ...
                     sprintf('%s_rms.mat', roi));

if ~exist(func_path, 'file')
    error('Functional data not found: %s', func_path);
end

load(func_path, 'rms_activation');  % Nx1 double
fprintf('  Activation range: [%.3f, %.3f]\n', min(rms_activation), max(rms_activation));

% =========================================================================
% Create Interactive Figure
% =========================================================================
fprintf('\nCreating interactive viewer...\n');

fig = figure('Name', sprintf('%s %s Interactive Viewer', subject_id, roi), ...
             'Position', [100, 100, 1400, 900], ...
             'Color', 'white', ...
             'NumberTitle', 'off', ...
             'MenuBar', 'none', ...
             'ToolBar', 'figure');

% Main axes for brain surface
ax = axes('Position', [0.05, 0.20, 0.90, 0.75]);

% -------------------------------------------------------------------------
% Plot Surface with Functional Overlay
% -------------------------------------------------------------------------
fprintf('  Rendering surface mesh...\n');

% Determine color scale (5th-95th percentile for robustness)
cmin = prctile(rms_activation, 5);
cmax = prctile(rms_activation, 95);

h_mesh = trisurf(F, V(:,1), V(:,2), V(:,3), rms_activation, ...
                'Parent', ax, ...
                'EdgeColor', 'none', ...
                'FaceColor', 'interp', ...
                'FaceAlpha', 0.9);

colormap(ax, hot);
caxis(ax, [cmin, cmax]);
h_cbar = colorbar(ax, 'Location', 'eastoutside');
ylabel(h_cbar, 'RMS Activation', 'FontSize', 12, 'FontWeight', 'bold');

% -------------------------------------------------------------------------
% ROI Outline Overlay
% -------------------------------------------------------------------------
fprintf('  Adding ROI outline...\n');

% Find faces that belong to ROI (at least one vertex in ROI)
roi_vertices = find(roi_label);
roi_faces_mask = any(ismember(F, roi_vertices), 2);
F_roi = F(roi_faces_mask, :);

hold(ax, 'on');
h_roi = trisurf(F_roi, V(:,1), V(:,2), V(:,3), ...
               'FaceColor', 'none', ...
               'EdgeColor', 'cyan', ...
               'LineWidth', 2.5, ...
               'Visible', 'on');
hold(ax, 'off');

fprintf('  ROI outline faces: %d\n', size(F_roi, 1));

% -------------------------------------------------------------------------
% Formatting and Lighting
% -------------------------------------------------------------------------
axis(ax, 'equal', 'off');
view(ax, -90, 0);  % Posterior view (default)
lighting(ax, 'gouraud');
material(ax, 'dull');
camlight(ax, 'headlight');

title(ax, sprintf('%s - %s (Posterior View)', subject_id, roi), ...
     'FontSize', 15, 'FontWeight', 'bold', 'Interpreter', 'none');

% Enable 3D rotation
rotate3d(ax, 'on');

% =========================================================================
% UI Control Panel
% =========================================================================
fprintf('  Creating control panel...\n');

ui_panel = uipanel('Position', [0.05, 0.02, 0.90, 0.15], ...
                   'Title', 'Interactive Controls', ...
                   'FontSize', 12, ...
                   'FontWeight', 'bold', ...
                   'BackgroundColor', [0.95, 0.95, 0.95]);

% Toggle ROI outline visibility
uicontrol('Parent', ui_panel, ...
         'Style', 'togglebutton', ...
         'String', 'ROI Outline ON', ...
         'Value', 1, ...
         'Position', [20, 50, 150, 40], ...
         'FontSize', 11, ...
         'Callback', @(src, ~) toggle_roi_visibility(src, h_roi));

% Cycle through standard views
uicontrol('Parent', ui_panel, ...
         'Style', 'pushbutton', ...
         'String', 'Cycle View', ...
         'Position', [190, 50, 120, 40], ...
         'FontSize', 11, ...
         'Callback', @(~, ~) cycle_view(ax));

% Reset to posterior view
uicontrol('Parent', ui_panel, ...
         'Style', 'pushbutton', ...
         'String', 'Reset View', ...
         'Position', [330, 50, 120, 40], ...
         'FontSize', 11, ...
         'Callback', @(~, ~) reset_view(ax, subject_id, roi));

% Adjust transparency
uicontrol('Parent', ui_panel, ...
         'Style', 'text', ...
         'String', 'Surface Alpha:', ...
         'Position', [470, 60, 100, 20], ...
         'FontSize', 10, ...
         'HorizontalAlignment', 'right', ...
         'BackgroundColor', [0.95, 0.95, 0.95]);

uicontrol('Parent', ui_panel, ...
         'Style', 'slider', ...
         'Min', 0, 'Max', 1, 'Value', 0.9, ...
         'Position', [580, 65, 150, 20], ...
         'Callback', @(src, ~) set(h_mesh, 'FaceAlpha', src.Value));

% Help text
uicontrol('Parent', ui_panel, ...
         'Style', 'text', ...
         'String', 'Mouse: Left-drag to rotate | Scroll to zoom | Right-drag to pan', ...
         'Position', [20, 10, 700, 25], ...
         'FontSize', 10, ...
         'FontAngle', 'italic', ...
         'HorizontalAlignment', 'left', ...
         'BackgroundColor', [0.95, 0.95, 0.95]);

fprintf('\n========================================\n');
fprintf('Viewer ready!\n');
fprintf('Use mouse to interact with 3D brain.\n');
fprintf('========================================\n\n');

end

% =========================================================================
% Callback Functions
% =========================================================================

function toggle_roi_visibility(src, h_roi)
    % Toggle ROI outline on/off
    if src.Value == 1
        set(h_roi, 'Visible', 'on');
        src.String = 'ROI Outline ON';
    else
        set(h_roi, 'Visible', 'off');
        src.String = 'ROI Outline OFF';
    end
end

function cycle_view(ax)
    % Cycle through standard anatomical views
    persistent view_idx;
    if isempty(view_idx)
        view_idx = 0;
    end

    views = {[-90, 0], [90, 0], [0, 90], [180, 0], [0, 0]};
    names = {'Posterior', 'Anterior', 'Dorsal', 'Ventral', 'Lateral'};

    view_idx = mod(view_idx, length(views)) + 1;
    view(ax, views{view_idx});

    % Update title
    current_title = get(get(ax, 'Title'), 'String');
    new_title = regexprep(current_title, '\(.*View\)', ...
                         sprintf('(%s View)', names{view_idx}));
    title(ax, new_title, 'FontSize', 15, 'FontWeight', 'bold', 'Interpreter', 'none');

    fprintf('View changed to: %s\n', names{view_idx});
end

function reset_view(ax, subject_id, roi)
    % Reset to default posterior view
    view(ax, -90, 0);
    title(ax, sprintf('%s - %s (Posterior View)', subject_id, roi), ...
         'FontSize', 15, 'FontWeight', 'bold', 'Interpreter', 'none');
    fprintf('View reset to: Posterior\n');
end
