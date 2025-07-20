import streamlit as st
from azure.identity import DefaultAzureCredential
from azure.mgmt.network import NetworkManagementClient
import ipaddress
import os
import pandas as pd
import requests
from streamlit_lottie import st_lottie

def extract_resource_group_from_id(resource_id):
    parts = resource_id.split("/")
    try:
        rg_index = parts.index("resourceGroups")
        return parts[rg_index + 1]
    except (ValueError, IndexError):
        return None

# Inject Azure Portal-like theme and custom CSS
st.markdown(
    '''
    <style>
    .stApp {
        background-color: #f3f6fb;
    }
    h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stTitle {
        color: #24292f;
    }
    .lottie-container {
        background: transparent !important;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #0078d4;
        color: #fff;
        border-radius: 4px;
        border: none;
        font-weight: 600;
        transition: background 0.2s;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #005a9e;
        color: #fff;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        color: #0078d4;
        transition: color 0.2s;
    }
    .stTabs [aria-selected="true"] {
        border-bottom: 3px solid #0078d4;
        color: #0078d4;
    }
    .stDataFrame, .stTable {
        border-radius: 8px;
        box-shadow: 0 2px 8px 0 rgba(0,120,212,0.08);
    }
    .stSidebar {
        background-color: #ffffff !important;
    }
    @media (prefers-color-scheme: dark) {
        .stApp {
            background-color: #1b1b1b;
        }
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stTitle {
            color: #f3f6fb !important;
        }
        .stDataFrame, .stTable {
            background-color: #23272e !important;
            color: #f3f6fb !important;
        }
        .stSidebar {
            background-color: #23272e !important;
            color: #f3f6fb !important;
        }
        .stButton>button, .stDownloadButton>button {
            background-color: #0078d4;
            color: #fff;
        }
        .stTabs [data-baseweb="tab"] {
            color: #7abaff;
        }
        .stTabs [aria-selected="true"] {
            border-bottom: 3px solid #7abaff;
            color: #7abaff;
        }
    }
    .st-bb, .st-cq, .st-cx, .st-cy, .st-cz, .st-da, .st-db, .st-dc, .st-dd, .st-de, .st-df, .st-dg, .st-dh, .st-di, .st-dj, .st-dk, .st-dl, .st-dm, .st-dn, .st-do, .st-dp, .st-dq, .st-dr, .st-ds, .st-dt, .st-du, .st-dv, .st-dw, .st-dx, .st-dy, .st-dz, .st-e0, .st-e1, .st-e2, .st-e3, .st-e4, .st-e5, .st-e6, .st-e7, .st-e8, .st-e9, .st-ea, .st-eb, .st-ec, .st-ed, .st-ee, .st-ef, .st-eg, .st-eh, .st-ei, .st-ej, .st-ek, .st-el, .st-em, .st-en, .st-eo, .st-ep, .st-eq, .st-er, .st-es, .st-et, .st-eu, .st-ev, .st-ew, .st-ex, .st-ey, .st-ez, .st-f0, .st-f1, .st-f2, .st-f3, .st-f4, .st-f5, .st-f6, .st-f7, .st-f8, .st-f9, .st-fa, .st-fb, .st-fc, .st-fd, .st-fe, .st-ff, .st-fg, .st-fh, .st-fi, .st-fj, .st-fk, .st-fl, .st-fm, .st-fn, .st-fo, .st-fp, .st-fq, .st-fr, .st-fs, .st-ft, .st-fu, .st-fv, .st-fw, .st-fx, .st-fy, .st-fz, .st-g0, .st-g1, .st-g2, .st-g3, .st-g4, .st-g5, .st-g6, .st-g7, .st-g8, .st-g9, .st-ga, .st-gb, .st-gc, .st-gd, .st-ge, .st-gf, .st-gg, .st-gh, .st-gi, .st-gj, .st-gk, .st-gl, .st-gm, .st-gn, .st-go, .st-gp, .st-gq, .st-gr, .st-gs, .st-gt, .st-gu, .st-gv, .st-gw, .st-gx, .st-gy, .st-gz, .st-h0, .st-h1, .st-h2, .st-h3, .st-h4, .st-h5, .st-h6, .st-h7, .st-h8, .st-h9, .st-ha, .st-hb, .st-hc, .st-hd, .st-he, .st-hf, .st-hg, .st-hh, .st-hi, .st-hj, .st-hk, .st-hl, .st-hm, .st-hn, .st-ho, .st-hp, .st-hq, .st-hr, .st-hs, .st-ht, .st-hu, .st-hv, .st-hw, .st-hx, .st-hy, .st-hz, .st-i0, .st-i1, .st-i2, .st-i3, .st-i4, .st-i5, .st-i6, .st-i7, .st-i8, .st-i9, .st-ia, .st-ib, .st-ic, .st-id, .st-ie, .st-if, .st-ig, .st-ih, .st-ii, .st-ij, .st-ik, .st-il, .st-im, .st-in, .st-io, .st-ip, .st-iq, .st-ir, .st-is, .st-it, .st-iu, .st-iv, .st-iw, .st-ix, .st-iy, .st-iz, .st-j0, .st-j1, .st-j2, .st-j3, .st-j4, .st-j5, .st-j6, .st-j7, .st-j8, .st-j9, .st-ja, .st-jb, .st-jc, .st-jd, .st-je, .st-jf, .st-jg, .st-jh, .st-ji, .st-jj, .st-jk, .st-jl, .st-jm, .st-jn, .st-jo, .st-jp, .st-jq, .st-jr, .st-js, .st-jt, .st-ju, .st-jv, .st-jw, .st-jx, .st-jy, .st-jz, .st-k0, .st-k1, .st-k2, .st-k3, .st-k4, .st-k5, .st-k6, .st-k7, .st-k8, .st-k9, .st-ka, .st-kb, .st-kc, .st-kd, .st-ke, .st-kf, .st-kg, .st-kh, .st-ki, .st-kj, .st-kk, .st-kl, .st-km, .st-kn, .st-ko, .st-kp, .st-kq, .st-kr, .st-ks, .st-kt, .st-ku, .st-kv, .st-kw, .st-kx, .st-ky, .st-kz, .st-l0, .st-l1, .st-l2, .st-l3, .st-l4, .st-l5, .st-l6, .st-l7, .st-l8, .st-l9, .st-la, .st-lb, .st-lc, .st-ld, .st-le, .st-lf, .st-lg, .st-lh, .st-li, .st-lj, .st-lk, .st-ll, .st-lm, .st-ln, .st-lo, .st-lp, .st-lq, .st-lr, .st-ls, .st-lt, .st-lu, .st-lv, .st-lw, .st-lx, .st-ly, .st-lz, .st-m0, .st-m1, .st-m2, .st-m3, .st-m4, .st-m5, .st-m6, .st-m7, .st-m8, .st-m9, .st-ma, .st-mb, .st-mc, .st-md, .st-me, .st-mf, .st-mg, .st-mh, .st-mi, .st-mj, .st-mk, .st-ml, .st-mm, .st-mn, .st-mo, .st-mp, .st-mq, .st-mr, .st-ms, .st-mt, .st-mu, .st-mv, .st-mw, .st-mx, .st-my, .st-mz, .st-n0, .st-n1, .st-n2, .st-n3, .st-n4, .st-n5, .st-n6, .st-n7, .st-n8, .st-n9, .st-na, .st-nb, .st-nc, .st-nd, .st-ne, .st-nf, .st-ng, .st-nh, .st-ni, .st-nj, .st-nk, .st-nl, .st-nm, .st-nn, .st-no, .st-np, .st-nq, .st-nr, .st-ns, .st-nt, .st-nu, .st-nv, .st-nw, .st-nx, .st-ny, .st-nz, .st-o0, .st-o1, .st-o2, .st-o3, .st-o4, .st-o5, .st-o6, .st-o7, .st-o8, .st-o9, .st-oa, .st-ob, .st-oc, .st-od, .st-oe, .st-of, .st-og, .st-oh, .st-oi, .st-oj, .st-ok, .st-ol, .st-om, .st-on, .st-oo, .st-op, .st-oq, .st-or, .st-os, .st-ot, .st-ou, .st-ov, .st-ow, .st-ox, .st-oy, .st-oz, .st-p0, .st-p1, .st-p2, .st-p3, .st-p4, .st-p5, .st-p6, .st-p7, .st-p8, .st-p9, .st-pa, .st-pb, .st-pc, .st-pd, .st-pe, .st-pf, .st-pg, .st-ph, .st-pi, .st-pj, .st-pk, .st-pl, .st-pm, .st-pn, .st-po, .st-pp, .st-pq, .st-pr, .st-ps, .st-pt, .st-pu, .st-pv, .st-pw, .st-px, .st-py, .st-pz, .st-q0, .st-q1, .st-q2, .st-q3, .st-q4, .st-q5, .st-q6, .st-q7, .st-q8, .st-q9, .st-qa, .st-qb, .st-qc, .st-qd, .st-qe, .st-qf, .st-qg, .st-qh, .st-qi, .st-qj, .st-qk, .st-ql, .st-qm, .st-qn, .st-qo, .st-qp, .st-qq, .st-qr, .st-qs, .st-qt, .st-qu, .st-qv, .st-qw, .st-qx, .st-qy, .st-qz, .st-r0, .st-r1, .st-r2, .st-r3, .st-r4, .st-r5, .st-r6, .st-r7, .st-r8, .st-r9, .st-ra, .st-rb, .st-rc, .st-rd, .st-re, .st-rf, .st-rg, .st-rh, .st-ri, .st-rj, .st-rk, .st-rl, .st-rm, .st-rn, .st-ro, .st-rp, .st-rq, .st-rr, .st-rs, .st-rt, .st-ru, .st-rv, .st-rw, .st-rx, .st-ry, .st-rz, .st-s0, .st-s1, .st-s2, .st-s3, .st-s4, .st-s5, .st-s6, .st-s7, .st-s8, .st-s9, .st-sa, .st-sb, .st-sc, .st-sd, .st-se, .st-sf, .st-sg, .st-sh, .st-si, .st-sj, .st-sk, .st-sl, .st-sm, .st-sn, .st-so, .st-sp, .st-sq, .st-sr, .st-ss, .st-st, .st-su, .st-sv, .st-sw, .st-sx, .st-sy, .st-sz, .st-t0, .st-t1, .st-t2, .st-t3, .st-t4, .st-t5, .st-t6, .st-t7, .st-t8, .st-t9, .st-ta, .st-tb, .st-tc, .st-td, .st-te, .st-tf, .st-tg, .st-th, .st-ti, .st-tj, .st-tk, .st-tl, .st-tm, .st-tn, .st-to, .st-tp, .st-tq, .st-tr, .st-ts, .st-tt, .st-tu, .st-tv, .st-tw, .st-tx, .st-ty, .st-tz, .st-u0, .st-u1, .st-u2, .st-u3, .st-u4, .st-u5, .st-u6, .st-u7, .st-u8, .st-u9, .st-ua, .st-ub, .st-uc, .st-ud, .st-ue, .st-uf, .st-ug, .st-uh, .st-ui, .st-uj, .st-uk, .st-ul, .st-um, .st-un, .st-uo, .st-up, .st-uq, .st-ur, .st-us, .st-ut, .st-uu, .st-uv, .st-uw, .st-ux, .st-uy, .st-uz, .st-v0, .st-v1, .st-v2, .st-v3, .st-v4, .st-v5, .st-v6, .st-v7, .st-v8, .st-v9, .st-va, .st-vb, .st-vc, .st-vd, .st-ve, .st-vf, .st-vg, .st-vh, .st-vi, .st-vj, .st-vk, .st-vl, .st-vm, .st-vn, .st-vo, .st-vp, .st-vq, .st-vr, .st-vs, .st-vt, .st-vu, .st-vv, .st-vw, .st-vx, .st-vy, .st-vz, .st-w0, .st-w1, .st-w2, .st-w3, .st-w4, .st-w5, .st-w6, .st-w7, .st-w8, .st-w9, .st-wa, .st-wb, .st-wc, .st-wd, .st-we, .st-wf, .st-wg, .st-wh, .st-wi, .st-wj, .st-wk, .st-wl, .st-wm, .st-wn, .st-wo, .st-wp, .st-wq, .st-wr, .st-ws, .st-wt, .st-wu, .st-wv, .st-ww, .st-wx, .st-wy, .st-wz, .st-x0, .st-x1, .st-x2, .st-x3, .st-x4, .st-x5, .st-x6, .st-x7, .st-x8, .st-x9, .st-xa, .st-xb, .st-xc, .st-xd, .st-xe, .st-xf, .st-xg, .st-xh, .st-xi, .st-xj, .st-xk, .st-xl, .st-xm, .st-xn, .st-xo, .st-xp, .st-xq, .st-xr, .st-xs, .st-xt, .st-xu, .st-xv, .st-xw, .st-xx, .st-xy, .st-xz, .st-y0, .st-y1, .st-y2, .st-y3, .st-y4, .st-y5, .st-y6, .st-y7, .st-y8, .st-y9, .st-ya, .st-yb, .st-yc, .st-yd, .st-ye, .st-yf, .st-yg, .st-yh, .st-yi, .st-yj, .st-yk, .st-yl, .st-ym, .st-yn, .st-yo, .st-yp, .st-yq, .st-yr, .st-ys, .st-yt, .st-yu, .st-yv, .st-yw, .st-yx, .st-yy, .st-yz, .st-z0, .st-z1, .st-z2, .st-z3, .st-z4, .st-z5, .st-z6, .st-z7, .st-z8, .st-z9, .st-za, .st-zb, .st-zc, .st-zd, .st-ze, .st-zf, .st-zg, .st-zh, .st-zi, .st-zj, .st-zk, .st-zl, .st-zm, .st-zn, .st-zo, .st-zp, .st-zq, .st-zr, .st-zs, .st-zt, .st-zu, .st-zv, .st-zw, .st-zx, .st-zy, .st-zz {
        border-radius: 8px !important;
        box-shadow: 0 2px 8px 0 rgba(0,120,212,0.08);
        transition: box-shadow 0.2s;
    }
    </style>
    ''',
    unsafe_allow_html=True
)

# Lottie animation (Azure cloud)
def load_lottieurl(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

lottie_azure = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_3vbOcw.json")

st.markdown('<div class="lottie-container">', unsafe_allow_html=True)
st_lottie(lottie_azure, height=120, key="azurecloud")
st.markdown('</div>', unsafe_allow_html=True)

st.set_page_config(page_title="Azure CIDR Agent", layout="wide")
st.title("Azure CIDR Agent Dashboard")

# Helper to authenticate and create client
def get_network_client(subscription_id):
    credential = DefaultAzureCredential()
    return NetworkManagementClient(credential, subscription_id)

# Caching for expensive Azure API calls
@st.cache_data(ttl=300)
def cached_fetch_subscriptions():
    from azure.mgmt.resource import SubscriptionClient
    credential = DefaultAzureCredential()
    sub_client = SubscriptionClient(credential)
    return [(sub.subscription_id, sub.display_name) for sub in sub_client.subscriptions.list()]

@st.cache_data(ttl=300)
def cached_fetch_vnets(_client):
    return list(_client.virtual_networks.list_all())

@st.cache_data(ttl=300)
def cached_fetch_nics(_client):
    return list(_client.network_interfaces.list_all())

@st.cache_data(ttl=300)
def cached_fetch_subnets(_client, rg_name, vnet_name):
    return list(_client.subnets.list(rg_name, vnet_name))

# Use cached functions in place of direct API calls

def fetch_subscriptions():
    return cached_fetch_subscriptions()

def fetch_vnets_and_subnets(client):
    vnets = cached_fetch_vnets(client)
    vnet_data = []
    for vnet in vnets:
        rg_name = extract_resource_group_from_id(vnet.id)
        vnet_name = vnet.name
        vnet_cidrs = vnet.address_space.address_prefixes
        subnets = cached_fetch_subnets(client, rg_name, vnet_name)
        for subnet in subnets:
            subnet_cidr = subnet.address_prefix
            subnet_name = subnet.name
            # Calculate total IPs in subnet
            try:
                net = ipaddress.ip_network(subnet_cidr)
                total_ips = net.num_addresses
            except Exception:
                total_ips = None
            used_ips = None
            vnet_data.append({
                "VNet Name": vnet_name,
                "VNet CIDR": ", ".join(vnet_cidrs),
                "Subnet Name": subnet_name,
                "Subnet CIDR": subnet_cidr,
                "Total IPs": total_ips,
                "Used IPs": used_ips
            })
    return vnet_data

def fetch_used_cidrs(client):
    used_cidrs = set()
    vnets = cached_fetch_vnets(client)
    for vnet in vnets:
        used_cidrs.update(vnet.address_space.address_prefixes)
        rg_name = extract_resource_group_from_id(vnet.id)
        for subnet in cached_fetch_subnets(client, rg_name, vnet.name):
            used_cidrs.add(subnet.address_prefix)
    return used_cidrs

def freeup_suggestions(client):
    vnets = cached_fetch_vnets(client)
    unused_vnets = []
    for vnet in vnets:
        rg_name = extract_resource_group_from_id(vnet.id)
        subnets = cached_fetch_subnets(client, rg_name, vnet.name)
        if not subnets:
            unused_vnets.append((vnet.name, vnet.address_space.address_prefixes, rg_name))
    return unused_vnets

def suggest_cidr(client, netmask):
    used_cidrs = set(fetch_used_cidrs(client))
    private_ranges = [
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('192.168.0.0/16'),
    ]
    for parent in private_ranges:
        for subnet in parent.subnets(new_prefix=netmask):
            if str(subnet) not in used_cidrs:
                overlap = False
                for used in used_cidrs:
                    if ipaddress.IPv4Network(used).overlaps(subnet):
                        overlap = True
                        break
                if not overlap:
                    return str(subnet)
    return None

def suggest_vnet_cidr(client, subnet_netmask, num_subnets):
    used_cidrs = set(fetch_used_cidrs(client))
    private_ranges = [
        ipaddress.IPv4Network('10.0.0.0/8'),
        ipaddress.IPv4Network('172.16.0.0/12'),
        ipaddress.IPv4Network('192.168.0.0/16'),
    ]
    # Calculate the minimum VNet prefix length that can fit num_subnets of subnet_netmask
    needed_addresses = 2 ** (32 - subnet_netmask) * num_subnets
    for parent in private_ranges:
        for vnet_prefix in range(subnet_netmask, parent.prefixlen - 1, -1):
            vnet_block_size = 2 ** (32 - vnet_prefix)
            if vnet_block_size < needed_addresses:
                break
            for vnet in parent.subnets(new_prefix=vnet_prefix):
                # Check if this VNet CIDR is available
                if str(vnet) in used_cidrs:
                    continue
                overlap = False
                for used in used_cidrs:
                    if ipaddress.IPv4Network(used).overlaps(vnet):
                        overlap = True
                        break
                if not overlap:
                    # Check if we can carve out num_subnets subnets of subnet_netmask from this VNet
                    subnets = list(vnet.subnets(new_prefix=subnet_netmask))
                    if len(subnets) >= num_subnets:
                        return str(vnet), [str(s) for s in subnets[:num_subnets]]
    return None, []

def get_vnet_choices(client):
    vnets = cached_fetch_vnets(client)
    return [(vnet.name, extract_resource_group_from_id(vnet.id), vnet.address_space.address_prefixes) for vnet in vnets]

def suggest_subnets_in_vnet(client, vnet_cidr, existing_subnet_cidrs, subnet_netmask, num_subnets):
    vnet_network = ipaddress.ip_network(vnet_cidr)
    used_networks = [ipaddress.ip_network(c) for c in existing_subnet_cidrs]
    possible_subnets = [s for s in vnet_network.subnets(new_prefix=subnet_netmask)
                        if not any(s.overlaps(u) for u in used_networks)]
    if len(possible_subnets) >= num_subnets:
        return [str(s) for s in possible_subnets[:num_subnets]]
    return []

def find_unused_subnets(client):
    nics = cached_fetch_nics(client)
    used_subnet_ids = set()
    for nic in nics:
        for ipconf in nic.ip_configurations:
            if ipconf.subnet and ipconf.subnet.id:
                used_subnet_ids.add(ipconf.subnet.id.lower())
    unused_subnets = []
    vnets = cached_fetch_vnets(client)
    for vnet in vnets:
        rg_name = extract_resource_group_from_id(vnet.id)
        for subnet in cached_fetch_subnets(client, rg_name, vnet.name):
            if subnet.id.lower() not in used_subnet_ids:
                unused_subnets.append({
                    "VNet Name": vnet.name,
                    "Subnet Name": subnet.name,
                    "Subnet CIDR": subnet.address_prefix,
                    "Resource Group": rg_name
                })
    return unused_subnets

# UI: Subscription selection
st.sidebar.header("Azure Subscription")
with st.spinner("Loading subscriptions..."):
    subscriptions = fetch_subscriptions()
if not subscriptions:
    st.error("No Azure subscriptions found or authentication failed. Please login with Azure CLI or set up your credentials.")
    st.stop()

sub_ids = {name: sid for sid, name in subscriptions}
selected_sub = st.sidebar.selectbox("Select Subscription", list(sub_ids.keys()))
subscription_id = sub_ids[selected_sub]

client = get_network_client(subscription_id)

# Tabs for features
tab1, tab2, tab3 = st.tabs(["Used CIDRs", "Free Up Suggestions", "Suggest CIDR"])

with tab1:
    with st.spinner("Loading VNet and subnet data..."):
        st.subheader("VNet and Subnet CIDR Usage Table")
        vnet_data = fetch_vnets_and_subnets(client)
        if vnet_data:
            df = pd.DataFrame(vnet_data)
            st.dataframe(df, use_container_width=True)
            st.subheader("Subnet IP Utilization (Total IPs)")
            chart_df = df[["VNet Name", "Subnet Name", "Total IPs"]].copy()
            chart_df = chart_df.dropna(subset=["Total IPs"])
            chart_df["Label"] = chart_df["VNet Name"] + "/" + chart_df["Subnet Name"]
            st.bar_chart(chart_df.set_index("Label")["Total IPs"])
        else:
            st.info("No VNets or subnets found in this subscription.")

with tab2:
    with st.spinner("Loading free up suggestions..."):
        st.subheader("Suggestions to Free Up CIDRs")
        unused_vnets = freeup_suggestions(client)
        unused_subnets = find_unused_subnets(client)
        if unused_vnets:
            st.write("VNets with no subnets (can be deleted to free CIDRs):")
            st.table(unused_vnets)
        else:
            st.success("No unused VNets found. All CIDRs are in use.")
        if unused_subnets:
            st.write("Subnets with no connected devices (0 IPs used, can be deleted to free IP space):")
            st.table(unused_subnets)
        else:
            st.success("No unused subnets found. All subnets have connected devices.")

with tab3:
    st.subheader("Suggest Optimal CIDR for New VNet or Subnets in Existing VNet")
    vnet_choices = get_vnet_choices(client)
    vnet_options = [f"{name} ({', '.join(cidrs)})" for name, _, cidrs in vnet_choices]
    vnet_options.insert(0, "[Create new VNet]")
    selected_vnet = st.selectbox("Select VNet (or create new)", vnet_options)
    netmask = st.number_input("Subnet Netmask (e.g., 24 for /24)", min_value=8, max_value=30, value=24)
    num_subnets = st.number_input("Number of subnets needed", min_value=1, max_value=256, value=1)
    if st.button("Suggest CIDR"):
        if selected_vnet == "[Create new VNet]":
            if num_subnets == 1:
                suggestion = suggest_cidr(client, netmask)
                if suggestion:
                    st.success(f"Suggested CIDR: {suggestion}")
                else:
                    st.error("No available CIDR found with the given netmask and zero IP wastage.")
            else:
                vnet_cidr, subnets = suggest_vnet_cidr(client, netmask, num_subnets)
                if vnet_cidr:
                    st.success(f"Suggested VNet CIDR: {vnet_cidr}")
                    st.write(f"Subnets of /{netmask} you can create:")
                    st.code("\n".join(subnets))
                else:
                    st.error("No available VNet CIDR found that can fit the requested number of subnets with the given netmask and zero IP wastage.")
        else:
            idx = vnet_options.index(selected_vnet) - 1
            vnet_name, vnet_rg, vnet_cidrs = vnet_choices[idx]
            # For simplicity, use the first CIDR block of the VNet
            vnet_cidr = vnet_cidrs[0]
            subnets = list(client.subnets.list(vnet_rg, vnet_name))
            existing_subnet_cidrs = [s.address_prefix for s in subnets]
            suggested = suggest_subnets_in_vnet(client, vnet_cidr, existing_subnet_cidrs, netmask, num_subnets)
            if suggested:
                st.success(f"Suggested subnets in {vnet_name} ({vnet_cidr}):")
                st.code("\n".join(suggested))
            else:
                st.error(f"No available subnets of /{netmask} found in {vnet_name} ({vnet_cidr}) that do not overlap with existing subnets.") 